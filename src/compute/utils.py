
import pandas as pd
from typing import Tuple

#TODO these code should be moved to a env file or a config file

def get_rssa_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
	item_popularity = pd.read_csv('algs/data/rssa/item_popularity.csv')   
	ave_item_score = pd.read_csv('algs/data/rssa/averaged_item_score_implicitMF.csv')

	return item_popularity, ave_item_score

def get_rssa_model_path() -> str:
	return 'algs/models/rssa/'

def get_rssa_ers_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
	item_popularity = pd.read_csv('algs/models/rssa/item_popularity.csv')
	ave_item_score = pd.read_csv('algs/models/rssa/averaged_item_score.csv')

	return item_popularity, ave_item_score

def get_cybered_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
	item_popularity = pd.read_csv('algs/data/cybered/item_popularity.csv')   
	ave_item_score = pd.read_csv('algs/data/cybered/averaged_item_score_implicitMF.csv')

	return item_popularity, ave_item_score

def get_cybered_model_path() -> str:
	return 'algs/models/cybered/'

def get_iers_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
	item_popularity = pd.read_csv('algs/data/iers/ieRS_item_popularity.csv')   
	emotionsg20 = pd.read_csv('algs/data/iers/ieRS_emotions_g20.csv')

	return item_popularity, emotionsg20

def get_iers_model_path() -> str:
	return 'algs/models/iers/'

def get_rating_data_path() -> str:
	return 'algs/data/iers/ieRS_ratings_g20.csv'

def get_pref_viz_model_path() -> str:
	return 'algs/models/prefviz/'

def get_pref_viz_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
	item_popularity = pd.read_csv('algs/models/prefviz/item_popularity.csv')   
	ave_item_score = pd.read_csv('algs/models/prefviz/averaged_item_score.csv')

	return item_popularity, ave_item_score