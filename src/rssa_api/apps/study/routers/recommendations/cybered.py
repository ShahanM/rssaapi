from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.rssa import AlternateRS
from compute.utils import *
from data.cybereddatabase import SessionLocal as CyberedSessionLocal
from data.models.schema.movieschema import MovieSchema, RatingsSchema
from data.movies import get_movie, get_movies, get_movies_by_ids

router = APIRouter()

def get_cybered_db():
	db = CyberedSessionLocal()
	try:
		yield db
	finally:
		db.close()

@router.get("/cybered/movies/", response_model=List[MovieSchema], tags=['cybered movie'])
async def read_cybered_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_cybered_db)):
	movies = get_movies(db, skip=skip, limit=limit)
	return movies

@router.post("/cybered/recommendation/", response_model=List[MovieSchema], tags=['cybered movie'])
async def create_cybered_recommendations(rated_movies: RatingsSchema, db: Session = Depends(get_cybered_db)):

	cybered_itm_pop, cybered_ave_scores = get_cybered_data()
	cybered_model_path = get_cybered_model_path()
	cybered = AlternateRS(cybered_model_path, cybered_itm_pop, cybered_ave_scores)

	# temporary for data out
	movie_ids = [movie.item_id for movie in rated_movies.ratings]
	pd.DataFrame(rated_movies.ratings).to_csv('rated_movies.csv')
	rateddeets = get_movies_by_ids(db, movie_ids)
	pd.DataFrame(rateddeets).to_csv('rateddeets.csv')

	rcs = cybered.get_condition_prediction(rated_movies.ratings, \
			rated_movies.user_id, rated_movies.rec_type, 144)
	rcsm = get_movies_by_ids(db, rcs)
	pd.DataFrame(rcsm).to_csv('recs.csv')

	recs = cybered.get_condition_prediction(rated_movies.ratings, \
			rated_movies.user_id, rated_movies.rec_type, rated_movies.num_rec)
	movies = get_movies_by_ids(db, recs)

	return movies

@router.get("/cybered/movies/{movie_id}", response_model=MovieSchema, tags=['cybered movie'])
async def read_cybered_movie(movie_id: int, db: Session = Depends(get_cybered_db)):
	movie = get_movie(db, movie_id)
	return movie

@router.post("/cybered/movies/", response_model=List[MovieSchema], tags=['cybered movie'])
async def read_cybered_movies_by_ids(movie_ids: List[int], db: Session = Depends(get_cybered_db)):
	movies = get_movies_by_ids(db, movie_ids)
	return movies
