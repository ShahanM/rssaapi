"""
This file contains all the RSSA-related functions and the API for the RSSA 
study.

@Author: Mehtab Iqbal (Shahan) and Lijie Guo
@Affiliation: School of Computing, Clemson University
"""

import pickle
from typing import List, Literal, Union

import numpy as np
import pandas as pd
from data.models.schema.movieschema import RatedItemSchema
from pydantic.dataclasses import dataclass
from scipy.spatial.distance import cosine
from .common import predict_discounted, get_user_feature, RSSABase, predict


@dataclass
class Preference:
	"""
	Represents a predicted or actual preference. `categories`
	is a list of classes that an item belongs to.
	"""
	item_id: str
	categories: Union[Literal["top_n"], Literal["controversial"], \
		Literal["hate"], Literal["hip"], Literal["no_clue"]]


class AlternateRS(RSSABase):
	def __init__(self, model_path:str, item_popularity, ave_item_score):
		super().__init__(model_path, item_popularity, ave_item_score)

		self.discounting_factor = \
			self.__init_discounting_factor(item_popularity)
		self.discounting_coefficient = 0.5 # FIXME: Parameterize

		self.prediction_functions = {
			0: self.predict_user_topN,
			1: self.predict_user_controversial_items,
			2: self.predict_user_hate_items,
			3: self.predict_user_hip_items,
			4: self.predict_user_no_clue_items
		}

	def __init_discounting_factor(self, item_popularity):
		"""
		Parameters
		----------
		items_popularity: pd.DataFrame
			['item', 'count', 'rank']
		"""
		max_count = item_popularity['count'].max()

		return 10 ** len(str(max_count))

	def get_condition_prediction(self, ratings: List[RatedItemSchema], \
		user_id: str, condition: int, num_rec:int) -> List[str]:
		"""
		Parameters
		----------
		ratings: List of RatedItemSchema
		user_id: User ID
		condition: 
			0: topN, 
			1: controversial, 
			2: hate, 
			3: hip, 
			4: no clue
		numRec: Number of recommendations to return
		
		Returns
		-------
		List of item IDs
		"""

		return self.prediction_functions[condition](ratings, user_id, num_rec)
			
	def get_predictions(self, ratings: List[RatedItemSchema], user_id: str) \
		-> pd.DataFrame:
		"""
		Parameters
		----------
		ratings: List of RatedItemSchema
		user_id: User ID

		Returns
		-------
		pd.DataFrame of predictions
		"""
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])
		new_ratings = pd.Series(np.array([np.float64(rating.rating) for rating \
			in ratings]), index=rated_items)
		
		_preds = predict_discounted(self.model, \
			self.item_popularity, user_id, new_ratings, self.discounting_factor)
		
		return _preds[~_preds['item'].isin(rated_items)]
	
	def predict_user_topN(self, ratings: List[RatedItemSchema], user_id, \
		n=10) -> List[int]:

		topN_discounted = self.get_predictions(ratings, user_id).head(n)

		return list(map(int, topN_discounted['item']))

	def predict_user_hate_items(self, ratings: List[RatedItemSchema], user_id, \
		n=10) -> List[int]:
		preds = self.get_predictions(ratings, user_id)
		
		preds = pd.merge(preds, self.ave_item_score, how='left', on='item')
		preds['margin_discounted'] = preds['ave_discounted_score'] \
			- preds['discounted_score']
		
		preds = preds\
				.sort_values(by='margin_discounted', ascending=False).head(n)
		
		return list(map(int, preds['item']))
	
	def predict_user_hip_items(self, ratings: List[RatedItemSchema], user_id, \
		n=10) -> List[str]:
		
		num_bs = 1000
		top_n = self.get_predictions(ratings, user_id).head(num_bs)

		hip_items = top_n.sort_values(by='count', ascending=True).head(n)

		return list(map(str, hip_items['item']))
		
	def predict_user_no_clue_items(self, ratings: List[RatedItemSchema], \
		user_id, n=10) -> List[str]:
		new_ratings = pd.Series([rating.rating for rating in ratings])
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])
		
		resampled = self.__high_std(user_id, new_ratings)
		resampled = resampled[~resampled['item'].isin(rated_items)]
		resampled = resampled.sort_values(by='std', \
				ascending=False).head(n)

		return list(map(str, resampled['item']))
	
	def predict_user_controversial_items(self, ratings: List[RatedItemSchema], \
		user_id, numRec=10) -> List[str]:
		_ratings = pd.Series([rating.rating for rating in ratings])
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])

		umat = self.model.user_features_
		users = self.model.user_index_

		print("USERS")
		print(users)

		user_features = get_user_feature(self.model, _ratings)

		# FIXME - parameterize
		distance_method = 'cosine'
		numNeighbors = 20

		neighbors = self.__find_neighbors(umat, users, user_features, \
			distance_method, numNeighbors)
		
		print("NEIGHBORS")
		print(neighbors)

		variance = self.__controversial(neighbors.user.unique())

		variance_wo_rated =  variance[~variance['item'].isin(rated_items)]
		controversial_items =  variance_wo_rated \
				.sort_values(by='variance', ascending=False).head(numRec)
		
		return list(map(str, controversial_items['item']))

	def __high_std(self, liveUserID, new_ratings):
		all_resampled_df = \
			pd.DataFrame(self.items, columns=['item'])
		
		n_models = 20
		for i in range(1, n_models+1):
			filename = f"{self.model_path}resampled_model_{i}.pkl"
			f_import = open(filename, 'rb')
			model = pickle.load(f_import)
			f_import.close()

			model.use_ratings = True # FIXME: Save the model with this flag

			items_in_sample = model.item_index_.to_numpy()

			resampled_preds = model.predict_for_user(liveUserID, \
				items_in_sample, new_ratings)
			
			resampled_df = resampled_preds.to_frame().reset_index()
			col = f"score{i}"
			resampled_df.columns = ['item', col]
			
			all_resampled_df = \
				pd.merge(all_resampled_df, resampled_df, how='left', on='item')
			
		preds_only_df = all_resampled_df.drop(columns=['item'])
		all_resampled_df['std'] = np.nanstd(preds_only_df, axis = 1)
		all_items_std_df = all_resampled_df[['item', 'std']]
		all_items_std_df = pd.merge(all_items_std_df, self.item_popularity, \
			how='left', on='item')
		
		return all_items_std_df
	
	def __similarity_user_features(self, umat, users, feature_newUser, \
		method='cosine'):
		'''
			ALS has already pre-weighted the user features/item features;
			Use either the Cosine distance(by default) or the Eculidean distance;
			umat: np.ndarray
			users: Int64Index
			feature_newUser: np.ndarray
		'''        
		nrows, ncols = umat.shape
		distance = []
		if method == 'cosine':
			distance = [cosine(umat[i, ], feature_newUser) \
				for i in range(nrows)]
		elif method == 'euclidean':
			distance = [np.linalg.norm(umat[i, ] - feature_newUser) \
				for i in range(nrows)]
				
		distance = pd.DataFrame({'user': users.values, 'distance': distance})

		return distance

	def __find_neighbors(self, umat, users, feature_newUser, distance_method, \
		num_neighbors):
		similarity = self.__similarity_user_features(umat, users, \
			feature_newUser, distance_method)
		neighbors_similarity = similarity\
			.sort_values(by='distance', ascending=True).head(num_neighbors)
		
		return neighbors_similarity
	
	def __controversial(self, users_neighbor):
		scores_df = pd.DataFrame(self.items, columns=['item'])
		for neighbor in users_neighbor:
			scores_df[str(neighbor)] = self.model.predict_for_user(neighbor, \
				self.items).to_numpy()

		scores_df['variance'] = np.nanvar(scores_df.iloc[:, 1:], axis = 1)
		scores_df = pd.merge(scores_df, \
			self.item_popularity, how='left', on='item')

		return scores_df


	def get_advisors_with_profile(self, ratings: List[RatedItemSchema], \
		user_id, numRec=10) -> dict:
		_ratings = pd.Series([rating.rating for rating in ratings])
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])

		umat = self.model.user_features_
		users = self.model.user_index_

		# print("USERS")
		# print(users)

		user_features = get_user_feature(self.model, _ratings)

		# FIXME - parameterize
		distance_method = 'cosine'
		numNeighbors = 200

		neighbors = self.__find_neighbors(umat, users, user_features, \
			distance_method, numNeighbors)
		

		
		print("NEIGHBORS")

		neighbors.sort_values(by='distance', ascending=False, inplace=True)
		print(neighbors)

		neighbors = neighbors.head(numRec)
		neighbors = neighbors['user'].tolist()

		advisors = {}
		advisor_preds = {}
		for neighbor in neighbors:
			preds = self.model.predict_for_user(neighbor, \
				self.items)
			preds = preds.to_frame().reset_index()
			dist = [cosine(preds[i, ], self.model.item_features) for i in range(preds.shape[0])]
			# TODO: check if we can use preds vector directly
			print(dist)
			preds.columns = ['item', 'score']
			preds = preds[~preds['item'].isin(rated_items)]
			preds = preds.sort_values(by='score', ascending=False).head(200)
			# advisors[neighbor] = preds.sort_values(by='score', \
			# 	ascending=False).head(10)['item'].tolist()
			advisors[neighbor] = preds.head(10)['item'].tolist()

		
			# TODO: find the movie that advisor would recommend
			# Options:
			# 1. item_features_[[top 200 movies for advisor], ]
			# -> distance measure with item_features_[[rated_items], ]
			# -> return the closest as a recommendation



		print(self.model.item_features_)
		print(self.model.item_index_)
		print('Item features ', self.model.item_features_.shape)
		print('Item index ', self.model.item_index_.shape)
		nrows, _ = self.model.item_features_.shape
		

		# adv_predictions = {}
		# for key, value in advisors.items():
		# 	# advratings = [(item_id, 5) for item_id in value]
		# 	rated_items = np.array(list(map(np.int64, value)))
		# 	advratings = np.array([np.float64(5) for _ \
		# 		in range(len(value))])
		# 	new_ratings = pd.Series(np.array([np.float64(5) for _ \
		# 		in range(len(value))]), index=rated_items)
		# 	adv_predictions[key] = predict(self.model, self.item_popularity, key, new_ratings)


		# print(adv_predictions)

		print(self.item_popularity.head())


		# adv_predictions = {}
		# for key, value in advisors.items():
		# 	distance = [cosine(self.model.item_index_[i, ], self.model.item_features_) \
		# 		for i in value]
		# 	adv_predictions[key] = distance
		
		# print(adv_predictions)

		print(self.model.item_features_[339, ])


		print(advisors)


		return advisors