import pickle
from typing import List, Literal, Union

import numpy as np
import pandas as pd
from data.models.schema.movieschema import RatedItemSchema
from pydantic.dataclasses import dataclass
from scipy.spatial.distance import cosine


@dataclass
class Preference:
    """
    Represents a predicted or actual preference. `categories`
    is a list of classes that an item belongs to.
    """
    item_id: str
    categories: Union[Literal["top_n"], Literal["controversial"], \
		Literal["hate"], Literal["hip"], Literal["no_clue"]]


class RSSACompute:
	def __init__(self, model_path:str, item_popularity, ave_item_score):
		self.item_popularity = item_popularity
		self.ave_item_score = ave_item_score
		self.items = item_popularity.item.unique()

		self.discounting_factor = \
			self.__init_discounting_factor(item_popularity)
		self.discounting_coefficient = 0.5

		self.model_path = model_path
		self.trained_model = self.__import_trained_model()

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
		user_id: int, condition: int, num_rec:int) -> List[int]:
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
			
	def get_predictions(self, ratings: List[RatedItemSchema], user_id) \
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
		
		RSSA_preds, _ = self.__predict_discounted(user_id, new_ratings)

		return RSSA_preds[~RSSA_preds['item'].isin(rated_items)]

	def __predict_discounted(self, liveUserID, new_ratings):    
		'''
		algo: trained implicitMF model
		liveUserID: str
		new_ratings: Series
		N: # of recommendations
		item_popularity: ['item', 'count', 'rank']
		'''
		als_implicit_preds, liveUser_feature = \
			self.trained_model.predict_for_user(liveUserID, self.items, \
				new_ratings)

		als_implicit_preds_df = als_implicit_preds.to_frame().reset_index()
		als_implicit_preds_df.columns = ['item', 'score']

		RSSA_preds_df = pd.merge(als_implicit_preds_df, self.item_popularity, \
			how='left', on='item')
		RSSA_preds_df['discounted_score'] = RSSA_preds_df['score'] \
			- self.discounting_coefficient \
				* (RSSA_preds_df['count']/self.discounting_factor)
		
		return RSSA_preds_df, liveUser_feature   

	def __get_discounted_topN(self, user_id: int, \
		ratings: List[RatedItemSchema], numRec=10) -> pd.DataFrame:
		RSSA_preds_noRatedItems = self.get_predictions(ratings, user_id)

		return RSSA_preds_noRatedItems.sort_values(\
			by='discounted_score', ascending=False).head(numRec)
	
	def predict_user_topN(self, ratings: List[RatedItemSchema], user_id, \
		numRec=10) -> List[int]:

		recs_topN_discounted = self.__get_discounted_topN(user_id, ratings, \
			numRec)

		return list(map(int, recs_topN_discounted['item']))

	def predict_user_hate_items(self, ratings: List[RatedItemSchema], user_id, \
		numRec=10) -> List[int]:
		RSSA_preds_noRatedItems = self.get_predictions(ratings, user_id)
		
		RSSA_preds_noRatedItems_with_ave = pd.merge(RSSA_preds_noRatedItems, \
			self.ave_item_score, how = 'left', on = 'item')
		RSSA_preds_noRatedItems_with_ave['margin_discounted'] = \
			RSSA_preds_noRatedItems_with_ave['ave_discounted_score'] \
				- RSSA_preds_noRatedItems_with_ave['discounted_score']
		
		# RSSA_preds_noRatedItems_with_ave['margin'] = \
		# 	RSSA_preds_noRatedItems_with_ave['ave_score'] \
		# 		- RSSA_preds_noRatedItems_with_ave['score']
		
		recs_hate_items_discounted = \
			RSSA_preds_noRatedItems_with_ave\
				.sort_values(by='margin_discounted', ascending=False)\
					.head(numRec)
		
		return list(map(int, recs_hate_items_discounted['item']))
    
	def predict_user_hip_items(self, ratings: List[RatedItemSchema], user_id, \
		numRec=10) -> List[str]:
		
		numTopN = 1000  
		RSSA_topN = self.__get_discounted_topN(user_id, ratings, numTopN)

		recs_hip_items_discounted = RSSA_topN.sort_values(by ='count', \
			ascending=True).head(numRec)

		return list(map(str, recs_hip_items_discounted['item']))

	def __high_std(self, liveUserID, new_ratings):
		# items = item_popularity.item.unique()
		all_items_resampled_preds_df = \
			pd.DataFrame(self.items, columns=['item'])
		
		numResampledModels = 20
		for i in range(1, numResampledModels):
			filename = f"{self.model_path}resampled_implictMF{i}.pkl"
			# filename = model_path + 'resampled_implictMF' + str(i) + '.pkl'
			f_import = open(filename, 'rb')
			algo = pickle.load(f_import)
			f_import.close()

			items_in_sample = algo.item_index_.to_numpy()
			resampled_preds, _ = algo.predict_for_user(liveUserID, \
				items_in_sample, new_ratings)
			resampled_preds_df = resampled_preds.to_frame().reset_index()
			# col = 'score' + str(i)
			col = f"score{i}"
			resampled_preds_df.columns = ['item', col]
			all_items_resampled_preds_df = \
				pd.merge(all_items_resampled_preds_df, resampled_preds_df, \
					how='left', on='item')
			
		preds_only_df = all_items_resampled_preds_df.drop(columns=['item'])
		all_items_resampled_preds_df['std'] = np.nanstd(preds_only_df, axis = 1)
		all_items_std_df = all_items_resampled_preds_df[['item', 'std']]
		all_items_std_df = pd.merge(all_items_std_df, self.item_popularity, \
			how='left', on='item')
		
		return all_items_std_df
		
	def predict_user_no_clue_items(self, ratings: List[RatedItemSchema], \
		user_id, numRec=10) -> List[str]:
		new_ratings = pd.Series(rating.rating for rating in ratings)
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])
		
		resampled_preds_high_std = self.__high_std(user_id, new_ratings)
		resampled_preds_high_std_noRated = \
			resampled_preds_high_std[~resampled_preds_high_std['item']\
				.isin(rated_items)]
		recs_no_clue_items = \
			resampled_preds_high_std_noRated.sort_values(by='std', \
				ascending=False).head(numRec)

		return list(map(str, recs_no_clue_items['item']))

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
		neighbor_scores_df = pd.DataFrame(self.items, columns = ['item'])
		for neighbor in users_neighbor:
			neighbor_scores_df[str(neighbor)] = self.trained_model\
				.predict_for_user(neighbor, self.items).to_numpy()

		neighbor_scores_df['variance'] = \
			np.nanvar(neighbor_scores_df.iloc[:, 1:], axis = 1)
		neighbor_scores_df = pd.merge(neighbor_scores_df, \
			self.item_popularity, how='left', on='item')

		return neighbor_scores_df		
    
	def predict_user_controversial_items(self, ratings: List[RatedItemSchema], \
		user_id, numRec=10) -> List[str]:
		new_ratings = pd.Series(rating.rating for rating in ratings)
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])

		umat = self.trained_model.user_features_
		users = self.trained_model.user_index_
		[_, liveUser_feature] = self.__predict_discounted(user_id, new_ratings)
		distance_method = 'cosine'
		numNeighbors = 20

		neighbors = self.__find_neighbors(umat, users, liveUser_feature, \
			distance_method, numNeighbors)

		variance_neighbors = self.__controversial(neighbors.user.unique())

		variance_neighbors_noRated =  \
			variance_neighbors[~variance_neighbors['item'].isin(rated_items)]
		recs_controversial_items =  \
			variance_neighbors_noRated\
				.sort_values(by='variance', ascending=False).head(numRec)
		
		return list(map(str, recs_controversial_items['item']))

	def __import_trained_model(self):
		f_import = open(self.model_path + 'implictMF.pkl', 'rb')
		trained_model = pickle.load(f_import)
		f_import.close()

		return trained_model
