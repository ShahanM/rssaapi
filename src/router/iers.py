from compute.iers import IERSCompute
from typing import List

from compute.rssa import RSSACompute
from compute.utils import *
from data.database import SessionLocal, engine
from data.cybereddatabase import engine as cybered_engine
from data.models.schema import MovieSchema, RatedItemSchema, RatingsSchema, EmotionInputSchema, EmotionDiscreteInputSchema, EmotionContinuousInputSchema
from data.movies import get_movie, get_movies, get_movies_by_ids, get_ers_movies, get_ers_movies_by_ids
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session


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


@router.get("/ers/movies/", response_model=List[MovieSchema])
async def read_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    movies = get_ers_movies(db, skip=skip, limit=limit)
    
    return movies

@router.post("/ers/recommendation/", response_model=List[MovieSchema])
async def create_recommendations(rated_movies: RatingsSchema, db: Session = Depends(get_db)):
    recs = iersalgs.predict_topN(rated_movies.ratings, \
            rated_movies.user_id, rated_movies.num_rec)
    movies = get_ers_movies_by_ids(db, recs)
    
    return movies

@router.post("/ers/updaterecommendations/", response_model=List[MovieSchema])
async def update_recommendations(rated_movies: EmotionInputSchema, db: Session = Depends(get_db)):
	recs = []
	if rated_movies.input_type == "discrete":
		print(rated_movies.emotion_input)
		emo_in = [EmotionDiscreteInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
		recs = iersalgs.predict_discrete_tuned_topN(rated_movies.ratings, \
			rated_movies.user_id, emo_in, rated_movies.num_rec)
	elif rated_movies.input_type == "continuous":
		print(rated_movies.emotion_input)
		emo_in = [EmotionContinuousInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
		recs = iersalgs.predict_continuous_tuned_topN(rated_movies.ratings, \
			rated_movies.user_id, emo_in, rated_movies.num_rec)
	movies = get_ers_movies_by_ids(db, recs)
	
	return movies