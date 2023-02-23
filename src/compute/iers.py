import pickle
from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import distance

from data.models.schema import (EmotionContinuousInputSchema,
                                EmotionDiscreteInputSchema, RatedItemSchema)


class IERSCompute:
	def __init__(self, model_path, item_popularity, iersg20):
		self.item_popularity = item_popularity
		self.iersg20 = iersg20

		self.model_path = model_path
		self.trained_model = self.__import_trained_model()

		self.emotion_tags = ['anger', 'anticipation', 'disgust', 'fear', \
			'joy', 'sadness', 'surprise', 'trust']
		self.item_emotions = self.iersg20.rename({'movie_id' : 'item'}, \
			axis = 1)

		self.num_topN = 200

	def __import_trained_model(self):
		'''
		Import trained model

		Returns
		-------
		trained_model : trained model
		'''
		f_import = open(self.model_path + 'ieRS_implictMF.pkl', 'rb')
		trained_model = pickle.load(f_import)
		f_import.close()

		return trained_model

	def get_predictions(self, ratings: List[RatedItemSchema], user_id: int) -> \
		pd.DataFrame:
		'''
		Get predictions

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID

		Returns
		-------
		predictions : pd.DataFrame
			Predictions
		'''
		rated_items = np.array([np.int64(rating.item_id) for rating in ratings])
		new_ratings = pd.Series(np.array([np.float64(rating.rating) for rating \
			in ratings]), index=rated_items)
		
		[RSSA_preds, liveUser_feature] = \
			self.__live_prediction(self.trained_model, user_id, new_ratings, \
				self.item_popularity)

		RSSA_preds_noRatedItems = \
			RSSA_preds[~RSSA_preds['item'].isin(rated_items)]
			
		return RSSA_preds_noRatedItems

	def predict_topN(self, ratings: List[RatedItemSchema], user_id, numRec) -> \
		List[int]:
		'''
		Predict top N items using the Tradional Top-N recommendation from the 
		RSSA discounted predictions

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID
		numRec : int
			Number of recommendations

		Returns
		-------
		topN : List[int]
			Top N items
		'''
		topN_discounted = self.__get_rssa_discounted_prediction(ratings, \
			user_id, numRec)
		
		return list(map(int, topN_discounted['item']))
	
	def predict_diverseN(self, ratings: List[RatedItemSchema], user_id: int, \
		numRec: int) -> List[int]:
		'''
		Predict diverse N items using the Diverse Top-N recommendation by
		diversifying the RSSA discounted predictions

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID

		Returns
		-------
		diverseN : List[int]
			Diverse N items
		'''
		diverseN = self.__predict_diverseN_by_emotion(ratings, \
			user_id, self.num_topN)
		
		return list(map(int, diverseN['item']))		

	def __live_prediction(self, algo, liveUserID, new_ratings, item_popularity):
		'''
		Make live prediction

		Parameters
		----------
		algo : trained model
			Trained implicitMF model
		liveUserID : int
			User ID
		new_ratings : pd.Series
			New movie ratings using the RatedItemSchema
		item_popularity : pd.DataFrame
			Item popularity

		Returns
		-------
		RSSA_preds : pd.DataFrame
			Predictions
		liveUser_feature : pd.DataFrame
			User feature
		'''
		items = item_popularity.item.unique()
		
		als_implicit_preds, liveUser_feature = \
			algo.predict_for_user(liveUserID, items, new_ratings)
		als_implicit_preds_df = als_implicit_preds.to_frame().reset_index()
		als_implicit_preds_df.columns = ['item', 'score']
		
		highest_count = item_popularity['count'].max()
		digit = 1
		while highest_count/(10 ** digit) > 1:
			digit = digit + 1
		denominator = 10 ** digit
		
		a = 0.5 ## updated Jul. 6, 2021
		als_implicit_preds_popularity_df = pd.merge(als_implicit_preds_df, \
			item_popularity, how = 'left', on = 'item')
		RSSA_preds_df = als_implicit_preds_popularity_df
		RSSA_preds_df['discounted_score'] = RSSA_preds_df['score'] - \
			a*(RSSA_preds_df['count']/denominator)
		
		return RSSA_preds_df, liveUser_feature
	
	def __get_rssa_discounted_prediction(self, ratings: List[RatedItemSchema], \
		user_id, numRec) -> pd.DataFrame:
		'''
		Get RSSA discounted predictions

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int	
			User ID
		numRec : int
			Number of recommendations

		Returns
		-------
		RSSA_preds : pd.DataFrame
			Predictions
		'''
		RSSA_preds_of_noRatedItems = self.get_predictions(ratings, user_id)
		discounted_preds_sorted = RSSA_preds_of_noRatedItems.sort_values(by = \
			'discounted_score', ascending = False)
		return discounted_preds_sorted.head(numRec)
	
	def __get_candidate_item(self, ratings: List[RatedItemSchema], \
			user_id) -> Tuple[pd.DataFrame, pd.DataFrame]:
		'''
		Get candidate items

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID

		Returns
		-------
		candidate_items : pd.DataFrame
			Candidate items
		candidate_item_emotions : pd.DataFrame
			Candidate item emotions
		'''
		n_discounted_candidates = self.__get_rssa_discounted_prediction(ratings, \
							user_id, self.num_topN)
		candidate_ids = n_discounted_candidates.item.unique()

		candidate_item_emotions = \
			self.item_emotions[self.item_emotions['item'].isin(candidate_ids)]

		# candidate_item_ids = candidate_item_emotions.item.unique()

		return n_discounted_candidates, candidate_item_emotions

	def __predict_tuned_topN(self, ratings: List[RatedItemSchema], user_id, \
		user_emotion_tags: List[str], user_emotion_vals: List[float], \
			sort_order: bool) -> pd.DataFrame:
		'''
		Predict top N items using the Top-N recommendation from the RSSA
		discounted predictions tuned by user emotion input
		
		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID
		user_emotion_tags : List[str]
			List of user emotion tags
		user_emotion_vals : List[float]
			List of user emotion values
		sort_order : bool
			Sort order
		numRec : int
			Number of recommendations

		Returns
		-------
		topN : pd.DataFrame
			Top N items
		'''
		# topN_discounted = self.__get_rssa_discounted_prediction(ratings, \
			# user_id, self.num_topN)
		# candidate_ids = topN_discounted.item.unique()

		# candidate_item_emotions = \
			# self.item_emotions[self.item_emotions['item'].isin(candidate_ids)]

		candidate_items, candidate_item_emotions = \
			self.__get_candidate_item(ratings, \
							user_id)

		# candidate_item_specified_emotions_ndarray = \
		# 	candidate_item_emotions[user_emotion_tags].to_numpy()

		# candidate_item_ids = candidate_item_emotions.item.unique()
		
		# distance_to_input = \
		# 	self.__emotion_distance(candidate_item_specified_emotions_ndarray, \
		# 		user_emotion_vals)
		# distance_to_input_df = pd.DataFrame({'item': candidate_item_ids, \
		# 	'distance': distance_to_input}, columns = ['item', 'distance'])
		# distance_to_input_df_sorted = \
		# 	distance_to_input_df.sort_values(by ='distance', \
		# 		ascending=sort_order)

		distance_to_input_df_sorted = self.__get_distance_to_input( \
			candidate_item_emotions, user_emotion_tags, user_emotion_vals, \
			sort_order)

		return distance_to_input_df_sorted
	
	def __get_distance_to_input(self, emotions_items, user_emotion_tags, \
			user_emotion_vals, sort_order) -> pd.DataFrame:
		'''
		Get distance to input

		Parameters
		----------
		emotions_ndarray : np.ndarray
			Emotion ndarray
		user_emotion_vals : List[float]
			List of user specified emotion values

		Returns
		-------
		distance_to_input : np.ndarray
			Distance to input
		'''
		emotion_item_ids = emotions_items.item.unique()

		emotions_items_ndarray = \
			emotions_items[user_emotion_tags].to_numpy()

		distance_to_input = \
			self.__emotion_distance(emotions_items_ndarray, \
				user_emotion_vals)
		
		distance_to_input_df = pd.DataFrame({'item': emotion_item_ids, \
			'distance': distance_to_input}, columns = ['item', 'distance'])
		distance_to_input_df_sorted = \
			distance_to_input_df.sort_values(by ='distance', \
				ascending=sort_order)
		
		return distance_to_input_df_sorted

	def __process_discrete_emotion_input(self, \
		emotion_input: List[EmotionDiscreteInputSchema]) \
		-> Tuple[List[str], List[str], List[float]]:
		'''
		Process discrete emotion input

		Parameters
		----------
		emotion_input : List[EmotionDiscreteInputSchema]
			List of discrete emotion input

		Returns
		-------
		user_emotion_tags : List[str]
			List of user emotion tags
		user_emotion_vals : List[float]
			List of user emotion values
		'''
		specified_emotion_tags = []
		specified_emotion_vals = []
		unspecified_emotion_tags = []
		emo_dict = {emo.emotion.lower(): emo.weight for emo in emotion_input}
		for emo in self.emotion_tags:
			if emo_dict[emo] == 'low':
				specified_emotion_tags.append(emo)
				specified_emotion_vals.append(0.3)
			elif emo_dict[emo] == 'high':
				specified_emotion_tags.append(emo)
				specified_emotion_vals.append(0.8)
			else:
				unspecified_emotion_tags.append(emo)
		
		return specified_emotion_tags, unspecified_emotion_tags, \
			specified_emotion_vals

	def predict_discrete_tuned_topN(self, ratings: List[RatedItemSchema], \
		user_id: int, emotion_input: List[EmotionDiscreteInputSchema], \
			numRec: int) -> List[int]:
		'''
		Predict top N items using the Top-N recommendation from the RSSA
		discounted predictions tuned by user emotion input
		
		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID
		emotion_input : List[EmotionDiscreteInputSchema]
			List of discrete emotion input
		numRec : int
			Number of recommendations

		Returns
		-------
		topN : List[int]
			Top N items
		'''
		user_specified_emotion_tags, _, user_specified_emotion_vals = self.\
				__process_discrete_emotion_input(emotion_input)
		
		tuned_topN = self.__predict_tuned_topN(ratings, user_id, \
			user_specified_emotion_tags, user_specified_emotion_vals, \
				True)
		
		return list(map(int, tuned_topN.head(numRec)['item']))

	def predict_continuous_tuned_topN(self, ratings: List[RatedItemSchema], \
		user_id, emotion_input: List[EmotionContinuousInputSchema], \
			numRec: int) -> List[int]:
		'''
		Predict top N items using the Top-N recommendation from the RSSA
		discounted predictions tuned by user emotion input

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID
		emotion_input : List[EmotionContinuousInputSchema]
			List of continuous emotion input
		numRec : int
			Number of recommendations

		Returns
		-------
		topN : List[int]
			Top N items
		'''
		user_emotion_tags = [one_emotion.emotion \
			for one_emotion in emotion_input]
		user_emotion_vals = [one_emotion.weight \
			for one_emotion in emotion_input]

		user_emotion_dict = dict(zip(user_emotion_tags, user_emotion_vals))

		user_specified_emotion_tags = []
		user_unspecified_emotion_tags = []
		user_specified_emotion_vals = []

		for k, v in user_emotion_dict.items():
			if v != 0:
				user_specified_emotion_tags.append(k)
				user_specified_emotion_vals.append(v)
			else: 
				user_unspecified_emotion_tags.append(k)
		
		tuned_topN = self.__predict_tuned_topN(ratings, user_id, \
			user_specified_emotion_tags, user_specified_emotion_vals, \
				False)
		
		return list(map(int, tuned_topN.head(numRec)['item']))

	def __predict_tuned_diverseN(self, ratings: List[RatedItemSchema], user_id, \
		user_emotion_tags: List[str], user_emotion_vals: List[float], \
		unspecified_emotion_tags: List[str], sort_order: bool, numDiv: int) \
			-> pd.DataFrame:
		'''
		Predict top N items using the diversified recommendation from the RSSA
		discounted predictions tuned by user emotion input

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID
		sort_oder : bool
			Sort order
		numRec : int
			Number of recommendations

		Returns
		-------
		topN : List[int]
			Top N items
		'''		
		candidate_items, candidate_item_emotions = \
			self.__get_candidate_item(ratings, \
			user_id)
		
		candidate_item_unspecified_emotions_ndarray = \
			candidate_item_emotions[unspecified_emotion_tags].to_numpy()
		
		# diverisfy emotions unspecified by user
		weighting = 0
		[diverseEmotion_unspecified, itemEmotion_unspecified] = \
			self.__diversify_item_feature(candidate_items, 
				candidate_item_unspecified_emotions_ndarray, \
					candidate_item_emotions.item.unique(), weighting, numDiv)
		

		# find similar items to user specified emotions
		candidates_for_similarity_ids = diverseEmotion_unspecified.item.unique()
		
		candidates_for_similarity_emotions = \
			candidate_item_emotions[candidate_item_emotions['item']\
			.isin(candidates_for_similarity_ids)]

		distance_to_input_df_sorted = self.__get_distance_to_input( \
			candidates_for_similarity_emotions, user_emotion_tags, \
			user_emotion_vals, sort_order)
		
		return distance_to_input_df_sorted


	def predict_discrete_tuned_diverseN(self, \
		ratings: List[RatedItemSchema], user_id: int, \
		emotion_input: List[EmotionDiscreteInputSchema], numRec: int) \
			-> List[int]:
		'''
		Predict top N items using the diversified recommendation from the RSSA
		discounted predictions tuned by user emotion input

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID
		emotion_input : List[EmotionDiscreteInputSchema]
			List of discrete emotion input
		numRec : int
			Number of recommendations

		Returns
		-------
		topN : List[int]
			Top N items
		'''

		user_specified_emotion_tags, user_unspecified_emotion_tags, \
			user_specified_emotion_vals = \
			self.__process_discrete_emotion_input(emotion_input)
		# tuned_topN, candidate_item_emotions = \
		# 	self.__predict_tuned_topN(ratings, user_id, \
		# 	user_specified_emotion_tags, user_specified_emotion_vals, \
		# 		True, 200)

		# topN_discounted = self.__get_rssa_discounted_prediction(ratings, \
			# user_id, 200)
		
		
		# candidate_item_specified_emotions_ndarray = \
		# 	candidate_item_emotions[user_specified_emotion_tags].to_numpy()

		# candidates_for_similarity_emotions_index = \
		# 	candidates_for_similarity_emotions.item.unique()
		rec_diverseEmotion = self.__predict_tuned_diverseN(ratings, user_id, \
			user_specified_emotion_tags, user_specified_emotion_vals, \
			user_unspecified_emotion_tags, True, 50)
		
		return list(map(int, rec_diverseEmotion.head(numRec)['item']))

	def __predict_diverseN_by_emotion(self, ratings: List[RatedItemSchema], \
		user_id:int, numRec: int) -> pd.DataFrame:
		'''
		Predict top N items using the diversified recommendation from the RSSA
		discounted predictions
		diversification by emotion

		Parameters
		----------
		ratings : List[RatedItemSchema]
			List of rated items
		user_id : int
			User ID
		numRec : int
			Number of recommendations

		Returns
		-------
		diverseTopN : pd.DataFrame
			Predicted diverse N items
		'''
		candidates = self.__get_rssa_discounted_prediction(ratings, user_id, \
			self.num_topN)[['item', 'discounted_score']]

		item_emotions_ndarray = self.item_emotions[self.emotion_tags].to_numpy()
		item_ids = self.item_emotions.item.unique()
		
		weighting = 0
		[rec_diverseEmotion, rec_itemEmotion] = \
			self.__diversify_item_feature(candidates, item_emotions_ndarray, \
				item_ids, weighting, numRec)
	
		return rec_diverseEmotion

	def __diversify_item_feature(self, candidates, vectors, items, weighting=0, \
		numRecs = 10, weight_sigma = None):
		'''
		Diversify items based on item features

		Parameters
		----------
		candidates : List[int]
			List of candidate items
		vectors : List[List[float]]
			List of item feature vectors
		items : List[int]
			List of item IDs
		weighting : float, optional
			Weighting factor, by default 0
		numRecs : int, optional
			Number of recommendations, by default 10
		weight_sigma : float, optional
			Weighting factor, by default None

		Returns
		-------
		diversified_items : List[int]
			List of diversified items
		'''
		itemID_values = candidates['item'].values
		candidates.index = pd.Index(itemID_values)
		
		if weighting != 0:
			if weight_sigma is not None :
				vectors = weight_sigma * vectors
		
		vectorsDf = pd.DataFrame(vectors)
		vectorsDf.index = pd.Index(items)
		vectorsDf_in_candidate = \
			vectorsDf[vectorsDf.index.isin(candidates.index)]
		
		# Sorting rows of vectorsDf_in_candidate by order of candidates
		candidate_vectorsDf = vectorsDf_in_candidate.reindex(candidates.index)
		
		# centroid and first candidate
		candidate_vectors = candidate_vectorsDf.to_numpy()
		items_candidate_vectors = candidate_vectorsDf.index.to_numpy()   
		centroid_vector = np.mean(candidate_vectors, axis = 0)
		
		diverse_itemIDs = []
		diverse_vectors = np.empty([0, vectors.shape[1]])
		
		firstItem_index_val = self.__first_item(centroid_vector, \
			candidate_vectors, items_candidate_vectors)
		firstItem_vector = \
			candidate_vectorsDf[candidate_vectorsDf.index.isin(\
				pd.Index([firstItem_index_val]))]
		diverse_vectors = np.concatenate((diverse_vectors, \
			firstItem_vector.to_numpy()), axis = 0)
		diverse_itemIDs.append(firstItem_index_val)
		
		candidate_vectorsDf_left = candidate_vectorsDf.drop(\
			pd.Index([firstItem_index_val]), axis = 0)
		
		# Find the best next item one by one
		while len(diverse_itemIDs) < numRecs:
			nextItem_vector, nextItem_index = \
				self.__sum_distance(candidate_vectorsDf_left, diverse_vectors)
			candidate_vectorsDf_left = candidate_vectorsDf_left.drop(
				pd.Index([nextItem_index]), axis = 0)
			diverse_vectors = np.concatenate((diverse_vectors, \
				nextItem_vector.to_numpy()), axis = 0)
			diverse_itemIDs.append(nextItem_index)

		diverse_itemIDs = np.asarray(diverse_itemIDs)

		diverse_itemIDsDf = pd.DataFrame({'item': diverse_itemIDs})
		diverse_itemIDsDf.index = pd.Index(diverse_itemIDs)

		diverse_vectorsDf = pd.DataFrame(diverse_vectors) 
		diverse_vectorsDf.index = pd.Index(diverse_itemIDs)

		diverse_items_shuffled = \
			candidates[candidates['item'].isin(diverse_itemIDs)]    
		recommendations = \
			diverse_items_shuffled.reindex(diverse_itemIDsDf.index)
		
		return recommendations, diverse_vectorsDf
        
	def __first_item(self, centroid, candidate_vectors, candidate_items):
		'''
		Find the first item

		Parameters
		----------
		centroid : np.ndarray
			Centroid vector
		candidate_vectors : np.ndarray
			List of candidate item feature vectors
		candidate_items : np.ndarray
			List of candidate item IDs

		Returns
		-------
		first_item : np.int64
			The index of the first item
		'''
		distance_cityblock = []
		for row in candidate_vectors:
			dist = self.__sqrt_cityblock(row, centroid)
			distance_cityblock.append(dist)
			
		distance_cityblock = pd.DataFrame({'distance': distance_cityblock})
		distance_cityblock.index = pd.Index(candidate_items)
		distance_cityblock_sorted = \
			distance_cityblock.sort_values(by='distance', ascending=True)
		first_index_val = distance_cityblock_sorted.index[0]
		return  first_index_val
        
	def __sum_distance(self, candidate_vectorsDf, diverse_set):
		'''
		Find the next best item

		Parameters
		----------
		candidate_vectorsDf : pd.DataFrame
			List of candidate item feature vectors
		diverse_set : np.ndarray
			List of diversified item feature vectors

		Returns
		-------
		bestItem_vector : pd.DataFrame
			Feature vector of the next best item
		bestItem_index : np.int64
			The index of the next best item
		'''
		distance_cumulate = []
		candidate_vectors = candidate_vectorsDf.to_numpy()
		for row_candidate_vec in candidate_vectors:
			sum_dist = 0
			for row_diverse in diverse_set:
				dist = self.__sqrt_cityblock(row_candidate_vec, row_diverse)
				sum_dist = sum_dist + dist
			distance_cumulate.append(sum_dist)
		distance_cumulate = pd.DataFrame({'sum_distance': distance_cumulate})
		distance_cumulate.index = candidate_vectorsDf.index
		distance_cumulate_sorted = \
			distance_cumulate.sort_values(by='sum_distance', ascending=False)
		bestItem_index = distance_cumulate_sorted.index[0]
		bestItem_vector = \
			candidate_vectorsDf[\
				candidate_vectorsDf.index.isin(pd.Index([bestItem_index]))]
		
		return bestItem_vector, bestItem_index
    
	def __sqrt_cityblock(self, point1, point2):
		'''
		Calculate the square root of the cityblock distance between two points

		Parameters
		----------
		point1 : np.ndarray
			Feature vector of the first point
		point2 : np.ndarray
			Feature vector of the second point

		Returns
		-------
		sqrt_cityblock : float
			Square root of the cityblock distance between the two points
		'''
		sqrt_city_block = 0
		for i in range(len(point1)):
			dist_axis = abs(point2[i] - point1[i])
			sqrt_city_block +=  dist_axis**(1/2)

		return sqrt_city_block  

	def __emotion_distance(self, matrix, vector):
		'''
		Calculate the distance between an emotion vector and the overall
		emotion matrix

		Parameters
		----------
		matrix : np.ndarray
			Overall emotion matrix
		vector : np.ndarray
			Emotion vector

		Returns
		-------
		distance : np.ndarray
			Distance between the emotion vector and the overall emotion matrix
		'''
		dist_array = []
		for row_vector in matrix:
			dist = distance.euclidean(row_vector, vector)
			dist_array.append(dist)
		
		return  dist_array
