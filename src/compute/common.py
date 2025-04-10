"""
This file contains all the RSSA-related functions and the API for the RSSA 
alternate algorithms.

@Author: Mehtab Iqbal (Shahan) and Lijie Guo
@Affiliation: School of Computing, Clemson University
"""
import pickle

import numpy as np
import pandas as pd
from lenskit.algorithms.als import ImplicitMF
from lenskit.algorithms.als import _train_implicit_row_lu as v_lu
from lenskit.algorithms.mf_common import MFPredictor
from scipy.spatial.distance import cosine


def predict(model: MFPredictor, items: pd.DataFrame, \
	user_id: str, ratings: pd.Series) -> pd.DataFrame:

	if isinstance(model, ImplicitMF):
		model.use_ratings = True # FIXME: We should save the model with this flag
	itemset = items.item.unique()

	als_preds = model.predict_for_user(user_id, itemset, ratings)

	# Convert the predictions to a dataframe
	als_preds = als_preds.to_frame().reset_index()
	als_preds.columns = ['item', 'score']

	print("als_preds: ", als_preds)

	return als_preds


def predict_discounted(model: ImplicitMF, items: pd.DataFrame, \
	userid: str, ratings: pd.Series, factor: int, coeff: float=0.5) \
	-> pd.DataFrame:
	"""Predict the ratings for the new items for the live user. 
	Discount the score of the items based on their popularity and
	compute the RSSA score.

	Parameters
	----------
	model: MFPredictor
		Trained model using a subclass of MFPredictor
	item_popularity: pd.DataFrame
		['item', 'count', 'rank']
	userid: str
		User ID of the live user
	new_ratings: pd.Series
		New ratings of the live user indexed by item ID
	factor: int
		Number of items to be considered for discounting. Typically,
		it the order of magnitude of the number of items in the
		dataset.
	coeff: float
		Discounting coefficient. Default value is 0.5.

	Returns
	-------
	pd.DataFrame
		['item', 'score', 'count', 'rank', 'discounted_score']
		The dataframe is sorted by the discounted_score in descending order.
	"""
	als_preds = predict(model, items, userid, ratings)

	# Merge the predictions with the item popularity dataframe for discounting
	als_preds = pd.merge(als_preds, items, how='left', on='item')
	als_preds['discounted_score'] = als_preds['score'] \
		- coeff * (als_preds['count']/factor)

	# Sort the predictions by the discounted score
	als_preds.sort_values(by='discounted_score', ascending=False, inplace=True)

	return als_preds


def get_user_feature(model: ImplicitMF, ratings):
	ri_idxes = model.item_index_.get_indexer_for(ratings.index)
	ri_good = ri_idxes >= 0
	ri_it = ri_idxes[ri_good]
	ri_val = ratings.values[ri_good]
	ri_val *= model.weight
	return v_lu(ri_it, ri_val, model.item_features_, model.OtOr_)


class RSSABase:
	def __init__(self, model_path:str, item_popularity, ave_item_score):
		self.item_popularity = item_popularity
		self.ave_item_score = ave_item_score
		self.items = item_popularity.item.unique()

		self.model_path = model_path
		self.model = self._import_trained_model()


	def _import_trained_model(self):
		f_import = open(self.model_path + 'model.pkl', 'rb')
		trained_model = pickle.load(f_import)
		f_import.close()

		return trained_model

	def _similarity_user_features(self, umat, users, feature_newUser, \
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

	def _find_neighbors(self, umat, users, feature_newUser, distance_method, \
		num_neighbors):
		similarity = self._similarity_user_features(umat, users, \
			feature_newUser, distance_method)
		neighbors_similarity = similarity\
			.sort_values(by='distance', ascending=True).head(num_neighbors)

		return neighbors_similarity


def scale_value(value, new_min, new_max, cur_min, cur_max):
	new_range = new_max - new_min
	cur_range = cur_max - cur_min
	new_value = new_range*(value - cur_min)/cur_range + new_min
	return new_value
