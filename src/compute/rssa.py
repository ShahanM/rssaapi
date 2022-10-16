import os
from typing import List, Literal
from pydantic.dataclasses import dataclass

import algs.rssa_recommendation as RSSA
from data.models.schema import RatedItemSchema
import pandas as pd
import numpy as np

@dataclass
class Preference:
    """
    Represents a predicted or actual preference. `categories`
    is a list of classes that an item belongs to.
    """
    item_id: str
    categories: List[Literal["top_n", "controversial", "hate", "hip", "no_clue"]]


class RSSACompute:
	def __init__(self):
		self.data_path = 'algs/data/'
		self.item_popularity = pd.read_csv(self.data_path + 'item_popularity.csv')    
		
		self.model_path = 'algs/models/'
		self.trained_model = RSSA.import_trained_model(self.model_path)

		self.ave_item_score = pd.read_csv(self.data_path + 'averaged_item_score_implicitMF.csv')

		self.prediction_functions = {
			0: self.predict_user_topN,
			1: self.predict_user_controversial_items,
			2: self.predict_user_hate_items,
			3: self.predict_user_hip_items,
			4: self.predict_user_no_clue_items
		}


	def get_condition_prediction(self, ratings: List[RatedItemSchema], user_id, condition, numRec=10):
		return self.prediction_functions[condition](ratings, user_id, numRec)
			

	def get_predictions(self, ratings: List[RatedItemSchema], user_id) -> pd.DataFrame:
		# Could we also put the item_popularity.csv into database as well?
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])
		new_ratings = pd.Series(np.array([np.float64(rating.rating) for rating in ratings]), index=rated_items)
		
		### Predicting
		[RSSA_preds, liveUser_feature] = RSSA.RSSA_live_prediction(self.trained_model, user_id, new_ratings, self.item_popularity)
		# ['item', 'score', 'count', 'rank', 'discounted_score']
		# liveUser_feature: ndarray    
		RSSA_preds_noRatedItems = RSSA_preds[~RSSA_preds['item'].isin(rated_items)]
		# ['item', 'score', 'count', 'rank', 'discounted_score']      
			
		return RSSA_preds_noRatedItems     


	def predict_user_topN(self, ratings: List[RatedItemSchema], user_id, numRec=10) -> List[Preference]:
		# numRec = 10
		RSSA_preds_noRatedItems = self.get_predictions(ratings, user_id)
		# ['item', 'score', 'count', 'rank', 'discounted_score']
		
		discounted_preds_sorted = RSSA_preds_noRatedItems.sort_values(by = 'discounted_score', ascending = False)
		recs_topN_discounted = discounted_preds_sorted.head(numRec)

		return list(map(str, recs_topN_discounted['item']))

	def predict_user_hate_items(self, ratings: List[RatedItemSchema], user_id, numRec=10) -> List[Preference]:
		# numRec = 10
		RSSA_preds_noRatedItems = self.get_predictions(ratings, user_id)
		# ['item', 'score', 'count', 'rank', 'discounted_score']
		
		# ['item', 'ave_score', 'ave_discounted_score']
		RSSA_preds_noRatedItems_with_ave = pd.merge(RSSA_preds_noRatedItems, self.ave_item_score, how = 'left', on = 'item')
		# ['item', 'score', 'count', 'rank', 'discounted_score', 'ave_score', 'ave_discounted_score']
		RSSA_preds_noRatedItems_with_ave['margin_discounted'] = RSSA_preds_noRatedItems_with_ave['ave_discounted_score'] - RSSA_preds_noRatedItems_with_ave['discounted_score']
		RSSA_preds_noRatedItems_with_ave['margin'] = RSSA_preds_noRatedItems_with_ave['ave_score'] - RSSA_preds_noRatedItems_with_ave['score']
		# ['item', 'score', 'count', 'rank', 'discounted_score', 'ave_score', 'ave_discounted_score', 'margin_discounted', 'margin']
		
		recs_hate_items_discounted = RSSA_preds_noRatedItems_with_ave.sort_values(by = 'margin_discounted', ascending = False).head(numRec)
		
		return list(map(str, recs_hate_items_discounted['item']))
    
    
	def predict_user_hip_items(self, ratings: List[RatedItemSchema], user_id, numRec=10) -> List[Preference]:
		# numRec = 10
		RSSA_preds_noRatedItems = self.get_predictions(ratings, user_id)
			# ['item', 'score', 'count', 'rank', 'discounted_score']
		numTopN = 1000    
		
		RSSA_preds_noRatedItems_sort_by_Dscore = RSSA_preds_noRatedItems.sort_values(by = 'discounted_score', ascending = False)
		
		RSSA_preds_noRatedItems_sort_by_Dscore_numTopN = RSSA_preds_noRatedItems_sort_by_Dscore.head(numTopN)
		# ['item', 'score', 'count', 'rank', 'discounted_score']  
		
		recs_hip_items_discounted = RSSA_preds_noRatedItems_sort_by_Dscore_numTopN.sort_values(by = 'count', ascending = True).head(numRec)
		# ['item', 'score', 'count', 'rank', 'discounted_score']     

		return list(map(str, recs_hip_items_discounted['item']))
    
		
	def predict_user_no_clue_items(self, ratings: List[RatedItemSchema], user_id, numRec=10) -> List[Preference]:
		# numRec = 10
		
		new_ratings = pd.Series(rating.rating for rating in ratings)
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])
		
		resampled_preds_high_std = RSSA.high_std(self.model_path, user_id, new_ratings, self.item_popularity)
			# ['item', 'std', 'count', 'rank'] 
		resampled_preds_high_std_noRated = resampled_preds_high_std[~resampled_preds_high_std['item'].isin(rated_items)]
		resampled_preds_high_std_noRated_sorted = resampled_preds_high_std_noRated.sort_values(by = 'std', ascending = False)
		recs_no_clue_items = resampled_preds_high_std_noRated_sorted.head(numRec)

		return list(map(str, recs_no_clue_items['item']))
		
    
	def predict_user_controversial_items(self, ratings: List[RatedItemSchema], user_id, numRec=10) -> List[Preference]:
		new_ratings = pd.Series(rating.rating for rating in ratings)
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])

		umat = self.trained_model.user_features_
		users = self.trained_model.user_index_
		### Predicting
		[_, liveUser_feature] = RSSA.RSSA_live_prediction(self.trained_model, user_id, new_ratings, self.item_popularity)
			# ['item', 'score', 'count', 'rank', 'discounted_score']
			# liveUser_feature: ndarray
		distance_method = 'cosine'
		numNeighbors = 20
		neighbors = RSSA.find_neighbors(umat, users, liveUser_feature, distance_method, numNeighbors)
			# ['user', 'distance']     
		variance_neighbors = RSSA.controversial(self.trained_model, neighbors.user.unique(), self.item_popularity)
			# ['item', 'variance', 'count', 'rank']    
		variance_neighbors_noRated =  variance_neighbors[~variance_neighbors['item'].isin(rated_items)]
		variance_neighbors_noRated_sorted =  variance_neighbors_noRated.sort_values(by = 'variance', ascending = False)
		recs_controversial_items = variance_neighbors_noRated_sorted.head(numRec)
		
		return list(map(str, recs_controversial_items['item']))