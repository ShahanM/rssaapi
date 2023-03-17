
import pandas as pd
from typing import Tuple


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
	return 'algs/models/cybered/'

def get_iers_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
	item_popularity = pd.read_csv('algs/data/iers/ieRS_item_popularity.csv')   
	emotionsg20 = pd.read_csv('algs/data/iers/ieRS_emotions_g20.csv')

	return item_popularity, emotionsg20

def get_iers_model_path() -> str:
	return 'algs/models/iers/'