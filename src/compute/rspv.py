"""
This file contains the RSSA Preference Visualization (RSPV) algorithms.

@Author: Mehtab Iqbal (Shahan)
@Affiliation: School of Computing, Clemson University
"""

from typing import List

from data.models.schema.movieschema import RatedItemSchema
import pandas as pd
import numpy as np
from .common import RSSABase, predict, scale_value
from pydantic import BaseModel
import itertools


class PreferenceItem(BaseModel):
	item_id: str
	community_score: float
	user_score: float
	community_label: int
	user_label: int


class PreferenceVisualization(RSSABase):
	def __init__(self, model_path:str, item_popularity, ave_item_score):
		super().__init__(model_path, item_popularity, ave_item_score)

	def get_prediction(self, ratings: List[RatedItemSchema], user_id) \
		-> pd.DataFrame:		
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])
		new_ratings = pd.Series(np.array([np.float64(rating.rating) for rating \
			in ratings]), index = rated_items)  
		
		als_preds = predict(self.model, self.item_popularity, \
			user_id, new_ratings)

		return als_preds
	
	def predict_diverse_items(self, ratings: List[RatedItemSchema], user_id) \
		-> List[PreferenceItem]:
		# Get user predictions
		preds = self.get_prediction(ratings, user_id)

		# Merge predcitions with the average item score
		preds = pd.merge(preds, self.ave_item_score, how='left', on='item')
		
		# Merge the predictions with the item popularity
		preds = pd.merge(preds, self.item_popularity, how ='left', on ='item')
		
		n_cutoff = 50
		candidates = preds[preds['count'] >= n_cutoff]

		n = 80 # number of items to be recommended
		# Apply the diversification algorithm
		diverse_items = self.__fishingnet(candidates, n_cutoff, n)
		
		scaled_items, scaled_avg_comm, scaled_avg_user = \
			self.scale_and_label(diverse_items)
			# diverse_items_rescared: ['item', 'score', 'ave_score', 'count',
			# 'rank', 'community', 'user', 'label_community', 'label_user']
		
		diverse_items = []
		for _, row in scaled_items.iterrows():
			diverse_items.append(PreferenceItem(
				item_id=str(int(row['item'])), # truncate the trailing .0
				community_score=row['community'],
				user_score=row['user'],
				community_label=row['community_label'],
				user_label=row['user_label']))

		return diverse_items

	def seeding(self, n, nb):
		ticks = [0]
		step = n / nb
		for i in range(nb):
			ticks.append(ticks[i]+step)
			
		return ticks

	def __fishingnet(self, candidates, cutoff=50, n=80):
		candidates.index = pd.Index(candidates['item'].values)
		candidates_vector = candidates[['score', 'ave_score']].to_numpy()
		
		ticks = self.seeding(5, 12) 
			# divide the 5 * 5 (predicted rating 0-5) grid into a 13*13 grid
		coordinates = list(itertools.product(ticks, ticks))
		coordinates = np.asarray(coordinates, dtype=np.float64)
		
		diverse_items = []

		# Greedy algorithm
		for point in coordinates:
			dist = np.sum(np.abs(candidates_vector - point), axis=1)
			idx_shortest_dist = np.argmin(dist)
			candidates_vector = np.delete(candidates_vector, \
				idx_shortest_dist, axis=0)

			item_idx = candidates.index[idx_shortest_dist]
			val_shortest_dist = dist[idx_shortest_dist]

			diverse_items.append(tuple((item_idx, val_shortest_dist)))
		
		diverse_items = sorted(diverse_items, key=lambda x: x[1])
		diverse_n_idx = [item[0] for item in diverse_items[:n]]

		diverse_items = candidates[candidates['item'].isin(diverse_n_idx)]

		return diverse_items
		
	def scale_and_label(self, items, new_min=1, new_max=5):
		
		scaled_items = items.copy()
		
		# Scale items to the target new range [new_min, new_max]
		_min = np.min([np.min(items['ave_score']), np.min(items['score'])])
		_max = np.max([np.max(items['ave_score']), np.max(items['score'])])

		scaled_items['community'] = scaled_items.apply(\
			lambda row: \
				scale_value(row['ave_score'], new_min, new_max, _min, _max), \
					axis=1)
		scaled_items['user'] = scaled_items.apply(\
			lambda row: \
				scale_value(row['score'], new_min, new_max, _min, _max), \
					axis=1)

		# Label the items based on the global average
		global_avg = np.mean([np.median(scaled_items['community']), \
			np.median(scaled_items['user'])])
		
		def label(row):
			row['community_label'] = 1 if row['community'] >= global_avg else 0
			row['user_label'] = 1 if row['user'] >= global_avg else 0
			return row
		
		labeled_items = scaled_items.apply(label, axis=1)
			
		labeled_items = labeled_items.astype({'item': 'int64', \
				'count': 'int64', 'rank': 'int64', 'community_label': 'int64', \
				'user_label': 'int64'})
		avg_comm_score = np.mean(labeled_items['community'])
		avg_user_score = np.mean(labeled_items['user'])
		
		return labeled_items, avg_comm_score, avg_user_score
