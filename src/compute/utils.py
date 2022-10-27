
import os
import pandas as pd
import algs.rssa_recommendation as rssa


def get_rssa_data():
	item_popularity = pd.read_csv('algs/data/rssa/item_popularity.csv')   
	ave_item_score = pd.read_csv('algs/data/rssa/averaged_item_score_implicitMF.csv')

	return item_popularity, ave_item_score

def get_rssa_model_path():

	return 'algs/models/rssa/'

def get_cybered_data():
	item_popularity = pd.read_csv('algs/data/cybered/item_popularity.csv')   
	ave_item_score = pd.read_csv('algs/data/cybered/averaged_item_score_implicitMF.csv')

	return item_popularity, ave_item_score

def get_cybered_model_path():
	model_path = os.path.join('algs', 'models/cybered/')

	return model_path