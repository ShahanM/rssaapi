from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from compute.iers import EmotionsRS
from data.moviedb import get_db as movie_db
from data.schemas.movie_schemas import MovieSchema
from data.schemas.preferences_schemas import (
	EmotionContinuousInputSchema,
	EmotionDiscreteInputSchema,
	EmotionInputSchema,
	EmotionInputSchemaExperimental,
	PreferenceRequestSchema,
	RatedItemSchema,
)
from docs.metadata import RSTagsEnum as Tags

router = APIRouter(
	prefix='/v2',
	tags=[Tags.rssa],
)

# TODO: Move to config file
TOP_N_TUNING_PARAMS = {
	'item_pool_size': 200,
	'scale_vector': False,  # scale vector only applicable for distance strategy
	'low_val': -0.125,
	'high_val': 0.125,
	'ranking_strategy': 'weighted',
	'distance_method': 'sqrtcityblock',  # only applicable for distance strategy
}

# TODO: Move to config file
DIVERSE_N_TUNING_PARAMS = {
	'item_pool_size': 200,
	'scale_vector': False,  # scale vector only applicable for distance strategy
	'diversity_sample_size': 100,
	'low_val': -0.125,
	'high_val': 0.125,
	'ranking_strategy': 'weighted',
	'diversity_criteria': 'unspecified',
	'distance_method': 'sqrtcityblock',  # only applicable for distance strategy
}


@router.post('/recommendation/ers/', response_model=List[MovieSchema])
async def generation_emotions_recommendation(user_ratings: PreferenceRequestSchema, db: Session = Depends(movie_db)):
	"""_summary_

	Args:
		rated_movies (NewRatingSchema): _description_
		db (Session, optional): _description_. Defaults to Depends(movie_db).

	Raises:
		HTTPException: _description_

	Returns:
		_type_: _description_
	"""
	iers_item_pop, iersg20 = get_iers_data()
	iers_model_path = get_iers_model_path()
	iersalgs = EmotionsRS(iers_model_path, iers_item_pop, iersg20)
	# recs: List[int] = []
	user_condition = 5
	ratins = {rat.item_id: rat.rating for rat in user_ratings.ratings}
	movies = get_ers_movies_by_ids_v2(db, list(ratins.keys()))
	newratins = [RatedItemSchema(item_id=int(m.movielens_id), rating=ratins[m.id]) for m in movies]
	if user_condition in [1, 2, 3, 4]:
		recs = iersalgs.predict_topN(newratins, user_ratings.user_id, user_ratings.num_rec)
	elif user_condition in [5, 6, 7, 8]:
		recs = iersalgs.predict_diverseN(
			ratings=newratins,
			user_id=1,
			num_rec=user_ratings.num_rec,
			dist_method=DIVERSE_N_TUNING_PARAMS['distance_method'],
			weight_sigma=0.0,
			item_pool_size=DIVERSE_N_TUNING_PARAMS['item_pool_size'],
			sampling_size=DIVERSE_N_TUNING_PARAMS['diversity_sample_size'],
		)
	recs = [str(rec) for rec in recs if rec is not None]
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail='User condition not found')
	movies = get_ers_movies_by_movielens_ids(db, recs)

	return movies


@router.put('/recommendations/ers/', response_model=List[MovieSchema])
async def update_recommendations(rated_movies: EmotionInputSchema, db: Session = Depends(movie_db)):
	iers_item_pop, iersg20 = get_iers_data()
	iers_model_path = get_iers_model_path()
	iersalgs = EmotionsRS(iers_model_path, iers_item_pop, iersg20)
	recs = []

	user_condition = 5
	ratins = {rat.item_id: rat.rating for rat in rated_movies.ratings}
	movies = get_ers_movies_by_ids_v2(db, list(ratins.keys()))
	newratins = [RatedItemSchema(item_id=int(m.movielens_id), rating=ratins[m.id]) for m in movies]
	if rated_movies.input_type == 'discrete':
		emo_in = [EmotionDiscreteInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
		if user_condition in [1, 2, 3, 4]:
			recs = iersalgs.predict_discrete_tuned_topN(
				ratings=newratins,
				user_id=1,
				emotion_input=emo_in,
				num_rec=rated_movies.num_rec,
				item_pool_size=TOP_N_TUNING_PARAMS['item_pool_size'],
				scale_vector=TOP_N_TUNING_PARAMS['scale_vector'],
				lowval=TOP_N_TUNING_PARAMS['low_val'],
				highval=TOP_N_TUNING_PARAMS['high_val'],
				ranking_strategy=TOP_N_TUNING_PARAMS['ranking_strategy'],
				dist_method=TOP_N_TUNING_PARAMS['distance_method'],
			)
		elif user_condition in [5, 6, 7, 8]:
			div_sample_size = DIVERSE_N_TUNING_PARAMS['diversity_sample_size']
			assert div_sample_size is not None
			recs = iersalgs.predict_discrete_tuned_diverseN(
				ratings=newratins,
				user_id=1,
				emotion_input=emo_in,
				num_rec=rated_movies.num_rec,
				sampling_size=div_sample_size,
				item_pool_size=DIVERSE_N_TUNING_PARAMS['diversity_sample_size'],
				scale_vector=DIVERSE_N_TUNING_PARAMS['scale_vector'],
				lowval=DIVERSE_N_TUNING_PARAMS['low_val'],
				highval=DIVERSE_N_TUNING_PARAMS['high_val'],
				ranking_strategy=DIVERSE_N_TUNING_PARAMS['ranking_strategy'],
				div_crit=DIVERSE_N_TUNING_PARAMS['diversity_criteria'],
				dist_method=DIVERSE_N_TUNING_PARAMS['distance_method'],
			)

	elif rated_movies.input_type == 'continuous':
		emo_in = [EmotionContinuousInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
		if rated_movies.user_condition in [1, 2, 3, 4]:
			recs = iersalgs.predict_continuous_tuned_topN(
				ratings=rated_movies.ratings,
				user_id=rated_movies.user_id,
				emotion_input=emo_in,
				num_rec=rated_movies.num_rec,
				item_pool_size=TOP_N_TUNING_PARAMS['item_pool_size'],
				scale_vector=TOP_N_TUNING_PARAMS['scale_vector'],
				algo=TOP_N_TUNING_PARAMS['ranking_strategy'],
				dist_method=TOP_N_TUNING_PARAMS['distance_method'],
			)
	recs = [str(rec) for rec in recs if rec is not None]
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail='User condition not found')

	movies = get_ers_movies_by_movielens_ids(db, recs)

	return movies


@router.put('/experimental/recommendations/', response_model=List[MovieSchema])
async def update_recommendations_experimental(
	rated_movies: EmotionInputSchemaExperimental, db: Session = Depends(movie_db)
):
	iers_item_pop, iersg20 = get_iers_data()
	iers_model_path = get_iers_model_path()
	iersalgs = EmotionsRS(iers_model_path, iers_item_pop, iersg20)
	recs = []
	if rated_movies.input_type == 'discrete':
		emo_in = [EmotionDiscreteInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
		if rated_movies.condition_algo == 1:
			recs = iersalgs.predict_discrete_tuned_topN(
				ratings=rated_movies.ratings,
				user_id=rated_movies.user_id,
				emotion_input=emo_in,
				num_rec=rated_movies.num_rec,
				item_pool_size=rated_movies.item_pool_size,
				scale_vector=rated_movies.scale_vector,
				lowval=rated_movies.low_val,
				highval=rated_movies.high_val,
				ranking_strategy=rated_movies.algo,
				dist_method=rated_movies.dist_method,
			)
		elif rated_movies.condition_algo == 2:
			div_sample_size = rated_movies.diversity_sample_size
			assert div_sample_size is not None
			recs = iersalgs.predict_discrete_tuned_diverseN(
				ratings=rated_movies.ratings,
				user_id=rated_movies.user_id,
				emotion_input=emo_in,
				num_rec=rated_movies.num_rec,
				sampling_size=div_sample_size,
				item_pool_size=rated_movies.item_pool_size,
				scale_vector=rated_movies.scale_vector,
				lowval=rated_movies.low_val,
				highval=rated_movies.high_val,
				ranking_strategy=rated_movies.algo,
				div_crit=rated_movies.diversity_criterion,
				dist_method=rated_movies.dist_method,
			)

	elif rated_movies.input_type == 'continuous':
		# Not implemented yet
		emo_in = [EmotionContinuousInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
		if rated_movies.condition_algo == 1:
			recs = iersalgs.predict_continuous_tuned_topN(
				ratings=rated_movies.ratings,
				user_id=rated_movies.user_id,
				emotion_input=emo_in,
				num_rec=rated_movies.num_rec,
				scale_vector=rated_movies.scale_vector,
				algo=rated_movies.algo,
				dist_method=rated_movies.dist_method,
				item_pool_size=rated_movies.item_pool_size,
			)

	recs = [str(rec) for rec in recs if rec is not None]
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail='User condition not found')

	movies = get_ers_movies_by_movielens_ids(db, recs)

	return movies
