from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from compute.iers import EmotionsRS
from compute.utils import *
from data.moviedatabase import SessionLocal
from data.models.schema.movieschema import *
from data.movies import *

router = APIRouter(prefix='/v1')

# TODO: Move to config file
TOP_N_TUNING_PARAMS = {
	'item_pool_size': 200,
	'scale_vector': False, # scale vector only applicable for distance strategy
	'low_val': -0.125,
	'high_val': 0.125,
	'ranking_strategy': 'weighted',
	'distance_method': 'sqrtcityblock' # only applicable for distance strategy
}
	
# TODO: Move to config file
DIVERSE_N_TUNING_PARAMS = {
	'item_pool_size': 200,
	'scale_vector': False, # scale vector only applicable for distance strategy
	'diversity_sample_size': 100,
	'low_val': -0.125,
	'high_val': 0.125,
	'ranking_strategy': 'weighted',
	'diversity_criteria': 'unspecified',
	'distance_method': 'sqrtcityblock' # only applicable for distance strategy
}


# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


@router.post('/ers/recommendation/', response_model=List[MovieSchema])
async def create_recommendations(rated_movies: RatingsSchema, \
	db: Session = Depends(get_db)):
	iers_item_pop, iersg20 = get_iers_data()
	iers_model_path = get_iers_model_path()
	iersalgs = EmotionsRS(iers_model_path, iers_item_pop, iersg20)
	recs: List[int] = []
	if rated_movies.user_condition in [1, 2, 3, 4]:
		recs = iersalgs.predict_topN(rated_movies.ratings, \
			rated_movies.user_id, rated_movies.num_rec)
	elif (rated_movies.user_condition in [5, 6, 7, 8]):
		recs = iersalgs.predict_diverseN(
			ratings=rated_movies.ratings, \
			user_id=rated_movies.user_id, 
			num_rec=rated_movies.num_rec, \
			dist_method=DIVERSE_N_TUNING_PARAMS['distance_method'], \
			weight_sigma=0.0,
			item_pool_size=DIVERSE_N_TUNING_PARAMS['item_pool_size'],
			sampling_size=DIVERSE_N_TUNING_PARAMS['diversity_sample_size'])
	
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail="User condition not found")
	movies = get_ers_movies_by_ids(db, recs)
	
	return movies


@router.post('/ers/updaterecommendations/', response_model=List[MovieSchema])
async def update_recommendations(rated_movies: EmotionInputSchema, \
	db: Session = Depends(get_db)):
	iers_item_pop, iersg20 = get_iers_data()
	iers_model_path = get_iers_model_path()
	iersalgs = EmotionsRS(iers_model_path, iers_item_pop, iersg20)
	recs = []
	if rated_movies.input_type == 'discrete':
		emo_in = [EmotionDiscreteInputSchema(**emoin.dict()) for emoin \
			in rated_movies.emotion_input]
		if rated_movies.user_condition in [1, 2, 3, 4]:
			recs = iersalgs.predict_discrete_tuned_topN(
				ratings=rated_movies.ratings, \
				user_id=rated_movies.user_id, \
				emotion_input=emo_in, \
				num_rec=rated_movies.num_rec, \
				item_pool_size=TOP_N_TUNING_PARAMS['item_pool_size'], \
				scale_vector=TOP_N_TUNING_PARAMS['scale_vector'], \
				lowval=TOP_N_TUNING_PARAMS['low_val'], \
				highval=TOP_N_TUNING_PARAMS['high_val'], \
				ranking_strategy=TOP_N_TUNING_PARAMS['ranking_strategy'], \
				dist_method=TOP_N_TUNING_PARAMS['distance_method'])
		elif (rated_movies.user_condition in [5, 6, 7, 8]):
			div_sample_size = DIVERSE_N_TUNING_PARAMS['diversity_sample_size']
			assert div_sample_size is not None
			recs = iersalgs.predict_discrete_tuned_diverseN( \
				ratings=rated_movies.ratings, \
				user_id=rated_movies.user_id, \
				emotion_input=emo_in, \
				num_rec=rated_movies.num_rec, \
				sampling_size=div_sample_size, \
				item_pool_size=DIVERSE_N_TUNING_PARAMS['diversity_sample_size'], \
				scale_vector=DIVERSE_N_TUNING_PARAMS['scale_vector'], \
				lowval=DIVERSE_N_TUNING_PARAMS['low_val'], \
				highval=DIVERSE_N_TUNING_PARAMS['high_val'], \
				ranking_strategy=DIVERSE_N_TUNING_PARAMS['ranking_strategy'],
				div_crit=DIVERSE_N_TUNING_PARAMS['diversity_criteria'],
				dist_method=DIVERSE_N_TUNING_PARAMS['distance_method'])
			
	elif rated_movies.input_type == 'continuous':
		emo_in = [EmotionContinuousInputSchema(**emoin.dict()) for emoin \
			in rated_movies.emotion_input]
		if rated_movies.user_condition in [1, 2, 3, 4]:
			recs = iersalgs.predict_continuous_tuned_topN(\
				ratings=rated_movies.ratings, \
				user_id=rated_movies.user_id, \
				emotion_input=emo_in, \
				num_rec=rated_movies.num_rec, \
				item_pool_size=TOP_N_TUNING_PARAMS['item_pool_size'], \
				scale_vector=TOP_N_TUNING_PARAMS['scale_vector'], \
				algo=TOP_N_TUNING_PARAMS['ranking_strategy'], \
				dist_method=TOP_N_TUNING_PARAMS['distance_method'])
	
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail="User condition not found")
	
	movies = get_ers_movies_by_ids(db, recs)
	
	return movies


@router.post('/ers/experimental/updaterecommendations/', \
	response_model=List[MovieSchema])
async def update_recommendations_experimental(\
	rated_movies: EmotionInputSchemaExperimental, db: Session = Depends(get_db)):
	iers_item_pop, iersg20 = get_iers_data()
	iers_model_path = get_iers_model_path()
	iersalgs = EmotionsRS(iers_model_path, iers_item_pop, iersg20)
	recs = []
	if rated_movies.input_type == 'discrete':
		emo_in = [EmotionDiscreteInputSchema(**emoin.dict()) for emoin \
			in rated_movies.emotion_input]
		if rated_movies.condition_algo == 1:
			recs = iersalgs.predict_discrete_tuned_topN(\
				ratings=rated_movies.ratings, \
				user_id=rated_movies.user_id, \
				emotion_input=emo_in, \
				num_rec=rated_movies.num_rec, \
				item_pool_size=rated_movies.item_pool_size, \
				scale_vector=rated_movies.scale_vector, \
				lowval=rated_movies.low_val, \
				highval=rated_movies.high_val,
				ranking_strategy=rated_movies.algo,
				dist_method=rated_movies.dist_method)
		elif rated_movies.condition_algo == 2:
			div_sample_size = rated_movies.diversity_sample_size
			assert div_sample_size is not None
			recs = iersalgs.predict_discrete_tuned_diverseN( \
				ratings=rated_movies.ratings, \
				user_id=rated_movies.user_id, \
				emotion_input=emo_in, \
				num_rec=rated_movies.num_rec, \
				sampling_size=div_sample_size, \
				item_pool_size=rated_movies.item_pool_size, \
				scale_vector=rated_movies.scale_vector, \
				lowval=rated_movies.low_val, \
				highval=rated_movies.high_val,
				ranking_strategy=rated_movies.algo,
				div_crit=rated_movies.diversity_criterion,
				dist_method=rated_movies.dist_method)
			
	elif rated_movies.input_type == 'continuous':
		# Not implemented yet
		emo_in = [EmotionContinuousInputSchema(**emoin.dict()) for emoin \
			in rated_movies.emotion_input]
		if rated_movies.condition_algo == 1:
			recs = iersalgs.predict_continuous_tuned_topN( \
			ratings=rated_movies.ratings, \
			user_id=rated_movies.user_id, \
			emotion_input=emo_in, \
			num_rec=rated_movies.num_rec, \
			scale_vector=rated_movies.scale_vector, \
			algo=rated_movies.algo, \
			dist_method=rated_movies.dist_method, \
			item_pool_size=rated_movies.item_pool_size)
	
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail="User condition not found")
	
	movies = get_ers_movies_by_ids(db, recs)
	
	return movies
