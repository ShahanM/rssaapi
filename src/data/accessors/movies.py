from sqlalchemy.orm import Session
from data.models.movies_v2 import Movie, MovieEmotions
from typing import List
from data.models.schema.movieschema import MovieSchema, MovieSchemaV2
from math import isnan
import uuid


def get_ers_movies_by_movielens_ids(db: Session, movielens_ids: list[str]) -> list[Movie]:
	# movielens_ids = list(map(str, movielens_ids))
	results = db.query(Movie, MovieEmotions)\
		.join(MovieEmotions, Movie.id == MovieEmotions.movie_id)\
		.filter(Movie.movielens_id.in_(movielens_ids))\
		.all()
	
	movies = [result[0] for result in results]
	# Order movies to the requested order
	movie_dict = {movie.movielens_id: movie for movie in movies}
	movies = [movie_dict[movielens_id] for movielens_id in movielens_ids]
	return movies


def get_all_ers_movies_v2(db: Session) -> List[Movie]:
	results = db.query(Movie, MovieEmotions)\
		.join(MovieEmotions, Movie.id == MovieEmotions.movie_id)\
		.all()
	
	return [result[0] for result in results]


def get_ers_movies_by_ids_v2(db: Session, movie_ids: List[uuid.UUID]) -> List[MovieSchemaV2]:
	results = db.query(Movie, MovieEmotions)\
		.join(MovieEmotions, Movie.id == MovieEmotions.movie_id)\
		.filter(Movie.id.in_(movie_ids))\
		.all()
	
	movies = [result[0] for result in results]
	# Order movies to the requested order
	movie_dict = {movie.id: movie for movie in movies}
	movies = [movie_dict[movie_id] for movie_id in movie_ids]
	return movies