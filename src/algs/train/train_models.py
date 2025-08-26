"""
This file contains the training script for the RSSA MFs.

@Author: Mehtab Iqbal (Shahan)
@Affiliation: School of Computing, Clemson University
"""

import argparse
import os
import pickle
import time

import numpy as np
import pandas as pd
from lenskit.algorithms import als


def load_training_data(data_path):
	ratings_train = pd.read_csv(data_path)
	col_rename_dict = {}
	if 'user_id' in ratings_train:
		col_rename_dict['user_id'] = 'user'
	elif 'userId' in ratings_train:
		col_rename_dict['userId'] = 'user'
	if 'movie_id' in ratings_train:
		col_rename_dict['movie_id'] = 'item'
	elif 'movieId' in ratings_train:
		col_rename_dict['movieId'] = 'item'

	ratings_train = ratings_train.rename(columns=col_rename_dict)

	return ratings_train


def load_training_data_npz(data_path):
	"""
	load the pre-saved npz file of the movie ratings
	"""
	model_loaded = np.load(data_path)
	data = model_loaded['dataset']
	trainset = pd.DataFrame(data, columns=['user', 'item', 'rating', 'timestamp'])
	trainset = trainset.astype({'user': int, 'item': int, 'rating': float, 'timestamp': int})

	return trainset


def __train_mf_model(training_data: pd.DataFrame, algo: str):
	model = None
	if algo == 'implicit':
		model = als.ImplicitMF(20, iterations=10, method='lu')
		model.fit(training_data)
	elif algo == 'explicit':
		model = als.BiasedMF(20)
		model.fit(training_data)

	if model is None:
		raise ValueError('Invalid algo: %s' % algo)

	return model


def __train_resampled_models(
	training_data: pd.DataFrame, algo: str, resample_count: int, output_dir: str, alpha: float = 0.5
):
	sample_size = int(training_data.shape[0] * alpha)

	print(f'\nTraining {resample_count} resampled models')
	start = time.time()

	for i in range(resample_count):
		print('\nTraining resampled model %d' % (i + 1))

		sample = training_data.sample(n=sample_size, replace=False)
		model = __train_mf_model(sample, algo)
		print(
			f'\nSerializing the trained model {i + 1} of {resample_count} \
			to disk.'
		)
		with open(f'{output_dir}/resampled_model_{i + 1}.pkl', 'wb') as f:
			pickle.dump(model, f)

	end = time.time() - start
	print('\nResampled models trained.')
	print('\nTime spent: %0.0fs' % end)


def __compute_ave_item_scores(model, training_data, item_popularity, alpha=0.2):
	items = training_data.item.unique()
	users = training_data.user.unique()

	discounting_factor = 10 ** len('%i' % item_popularity['count'].max())

	start = time.time()

	ave_scores_df = pd.DataFrame(items, columns=['item'])
	ave_scores_df['ave_score'] = 0
	ave_scores_df['ave_discounted_score'] = 0

	calculated_users = -1
	for user in users:
		calculated_users += 1
		user_implicit_preds = model.predict_for_user(user, items)

		user_df = user_implicit_preds.to_frame().reset_index()
		user_df.columns = ['item', 'score']
		user_df = pd.merge(user_df, item_popularity, how='left', on='item')
		user_df['discounted_score'] = user_df['score'] - alpha * (user_df['count'] / discounting_factor)

		ave_scores_df['ave_score'] = (ave_scores_df['ave_score'] * calculated_users + user_df['score']) / (
			calculated_users + 1
		)

		ave_scores_df['ave_discounted_score'] = (
			ave_scores_df['ave_discounted_score'] * calculated_users + user_df['discounted_score']
		) / (calculated_users + 1)

	print('\nTime spent: %0.0fs' % (time.time() - start))

	return ave_scores_df


def __main(
	data_path: str, model_path: str, algo: str, item_popularity: bool, ave_item_score: bool, resample_count: int
):
	train_data = load_training_data(data_path)

	## 1 - Discounting the input ratings by ranking
	# 1.1 - Calculating item rating counts and popularity rank,
	# This will be used to discount the popular items from the input side
	items, rating_counts = np.unique(train_data['item'], return_counts=True)
	item_ratings = sorted(zip(items, rating_counts), key=lambda x: x[1], reverse=True)

	itemranks = []
	current_rank = 1
	current_count = item_ratings[0][1]
	for item, count in item_ratings:
		if count < current_count:
			current_rank += 1
		itemranks.append((item, count, current_rank))
		current_count = count

	items_popularity = pd.DataFrame(itemranks, columns=['item', 'count', 'rank'])

	# 1.2 - Start to discounting the input ratings by ranking
	b = 0.4
	rpopularity = pd.merge(train_data, items_popularity, how='left', on='item')
	rpopularity['discounted_rating'] = rpopularity['rating'] * (1 - b / (2 * rpopularity['rank']))
	rtrain = rpopularity[['user', 'item', 'discounted_rating', 'timestamp']]
	rtrain = rtrain.rename({'discounted_rating': 'rating'}, axis=1)

	## 2 - Train the MF model
	print(f'Training {algo} MF models')
	start = time.time()

	model = __train_mf_model(rtrain, algo)

	end = time.time() - start
	print('\nMF model trained.')
	print('\nTime spent: %0.0fs' % end)

	print('\nSerializing the trained model to disk.')
	if not os.path.exists(model_path):
		os.makedirs(model_path)
	with open(f'{model_path}/model.pkl', 'wb') as f:
		pickle.dump(model, f)

	if item_popularity:
		print('\nSaving the item popularity as a csv file')
		items_popularity.to_csv(f'{model_path}/item_popularity.csv', index=False)

	if resample_count is not None:
		__train_resampled_models(rtrain, algo, resample_count, model_path)

	if ave_item_score:
		print('\nComputing the average item scores')
		scores_df = __compute_ave_item_scores(model, rtrain, items_popularity)
		print('\nSaving the average item scores as a csv file')
		scores_df.to_csv(f'{model_path}/averaged_item_score.csv', index=False)

	print('\nDone\n')


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Train MF models for RSSA algorithms.')
	parser.add_argument(
		'-d',
		'--data_path',
		type=str,
		required=True,
		help='Path to the csv training data containing the user ratings. \
			Each row is a rating record of a user on an item. \
			Columns: [user_id, movie_id, rating, timestamp]',
	)
	parser.add_argument(
		'-o', '--model_path', type=str, required=True, help='Path to the folder to save the trained model.'
	)
	parser.add_argument(
		'-a',
		'--algo',
		type=str,
		required=True,
		choices=['implicit', 'explicit'],
		help='Specify the MF algorithm to use.',
	)

	parser.add_argument(
		'--item_popularity',
		type=bool,
		required=True,
		action=argparse.BooleanOptionalAction,
		default=False,
		help='Specify whether to save the item popularity as a csv file.',
	)
	parser.add_argument(
		'--ave_item_score',
		type=bool,
		required=True,
		action=argparse.BooleanOptionalAction,
		default=False,
		help='Specify whether to generate the average item score for users.',
	)

	parser.add_argument(
		'-r',
		'--resample_count',
		type=int,
		required=False,
		help='Specify the number of resampled models to train in \
		addition to the model trained on the entire training data.\n \
		If not specified, then only one model will be trained on the \
		entire training data.',
	)

	args = parser.parse_args()
	__main(args.data_path, args.model_path, args.algo, args.item_popularity, args.ave_item_score, args.resample_count)

	# ieRS
	# --algo 'implicit'
	# --item_popularity
	# --ave_item_score

	# alt algo
	# --algo 'implicit'
	# --item_popularity
	# --ave_item_score
	# --resample_count 20

	# pref viz
	# --algo 'explicit'
	# --item_popularity
	# --ave_item_score
