from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from compute.iers import IERSCompute
from compute.utils import *
from data.moviedatabase import SessionLocal
from data.models.schema import *
from data.movies import *

router = APIRouter()

iers_item_pop, iersg20 = get_iers_data()
iers_model_path = get_iers_model_path()
iersalgs = IERSCompute(iers_model_path, iers_item_pop, iersg20)


# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
		

@router.get('/ers/movies/ids/', response_model=List[int], tags=['ers movie'])
async def read_movies_ids(db: Session = Depends(get_db)):
	movies = get_all_ers_movies(db)
	ids = [movie.movie_id for movie in movies]
	return ids


@router.get('/ers/movies/', response_model=List[MovieSchema], tags=['ers movie'])
async def read_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
	movies = get_ers_movies(db, skip=skip, limit=limit)
	
	return movies


@router.post('/ers/movies/', response_model=List[MovieSchema], tags=['ers movie'])
async def read_movies_by_ids(movie_ids: List[int], db: Session = Depends(get_db)):
	movies = get_ers_movies_by_ids(db, movie_ids)
	
	return movies


@router.post('/ers/recommendation/', response_model=List[MovieSchema], tags=['ers movie'])
async def create_recommendations(rated_movies: RatingsSchema, db: Session = Depends(get_db)):
	recs: List[int] = []
	if rated_movies.user_condition in [1, 2, 3, 4]:
		recs = iersalgs.predict_topN(rated_movies.ratings, \
			rated_movies.user_id, rated_movies.num_rec)
	elif (rated_movies.user_condition in [5, 6, 7, 8]):
		recs = iersalgs.predict_diverseN(rated_movies.ratings, \
			rated_movies.user_id, rated_movies.num_rec)
	
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail="User condition not found")
	movies = get_ers_movies_by_ids(db, recs)
	
	return movies


@router.post('/ers/updaterecommendations/', response_model=List[MovieSchema], tags=['ers movie'])
async def update_recommendations(rated_movies: EmotionInputSchema, db: Session = Depends(get_db)):
	recs = []
	if rated_movies.input_type == 'discrete':
		emo_in = [EmotionDiscreteInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]

		if rated_movies.user_condition in [1, 2, 3, 4]:
			recs = iersalgs.predict_discrete_tuned_topN(rated_movies.ratings, \
				rated_movies.user_id, emo_in, rated_movies.num_rec)
		elif (rated_movies.user_condition in [5, 6, 7, 8]):
			recs = iersalgs.predict_discrete_tuned_diverseN(rated_movies.ratings, \
				rated_movies.user_id, emo_in, rated_movies.num_rec)
			
	elif rated_movies.input_type == 'continuous':
		emo_in = [EmotionContinuousInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
		if rated_movies.user_condition in [1, 2, 3, 4]:
			recs = iersalgs.predict_continuous_tuned_topN(rated_movies.ratings, \
				rated_movies.user_id, emo_in, rated_movies.num_rec)
	
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail="User condition not found")
	movies = get_ers_movies_by_ids(db, recs)
	
	return movies



@router.post('/ers/experimental/updaterecommendations/', response_model=List[MovieSchema], tags=['ers movie'])
async def update_recommendations_experimental(rated_movies: EmotionInputSchemaExperimental, db: Session = Depends(get_db)):
	recs = []
	if rated_movies.input_type == 'discrete':
		emo_in = [EmotionDiscreteInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]

		if rated_movies.condition_algo == 1:
			recs = iersalgs.predict_discrete_tuned_topN(\
				ratings=rated_movies.ratings, \
				user_id=rated_movies.user_id, \
				emotion_input=emo_in, \
				num_rec=rated_movies.num_rec, \
				scale_vector=rated_movies.scale_vector, \
				lowval=rated_movies.low_val, \
				highval=rated_movies.high_val,
				algo=rated_movies.algo)
		elif rated_movies.condition_algo == 2:
			recs = iersalgs.predict_discrete_tuned_diverseN( \
				ratings=rated_movies.ratings, \
				user_id=rated_movies.user_id, \
				emotion_input=emo_in, \
				num_rec=rated_movies.num_rec, \
				scale_vector=rated_movies.scale_vector, \
				lowval=rated_movies.low_val, \
				highval=rated_movies.high_val,
				algo=rated_movies.algo)
			
	elif rated_movies.input_type == 'continuous':
		emo_in = [EmotionContinuousInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
		if rated_movies.condition_algo == 1:
			recs = iersalgs.predict_continuous_tuned_topN(rated_movies.ratings, \
				rated_movies.user_id, emo_in, rated_movies.num_rec)
	
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail="User condition not found")
	movies = get_ers_movies_by_ids(db, recs)
	
	return movies