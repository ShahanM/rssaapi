from sqlalchemy.orm import Session
from sqlalchemy import func
from data.models.movies_v2 import Movie, MovieEmotions, MovieRecommendationText
from typing import List, Union
import pydantic
from pydantic import BaseModel, Field, AliasChoices
from data.models.schemas.movieschema import MovieSchema, MovieSchemaV2
from math import isnan
import uuid


class MovieRecommendationSchema(BaseModel):
	id: uuid.UUID
	movie_id: uuid.UUID
	formal: str
	informal: str
	source: str
	model: str

	class Config:
		from_attributes = True
		orm_mode = True


def get_ers_movies_by_movielens_ids(db: Session, movielens_ids: list[str]) -> list[MovieSchemaV2]:
	results = db.query(Movie, MovieEmotions)\
		.join(MovieEmotions, Movie.id == MovieEmotions.movie_id)\
		.filter(Movie.movielens_id.in_(movielens_ids))\
		.all()
	
	movies = [result[0] for result in results]

	# Order movies to the requested order
	movie_dict = {movie.movielens_id: movie for movie in movies}
	movies = [MovieSchemaV2.model_validate(movie_dict[movielens_id]) for movielens_id in movielens_ids]
	return movies


def get_all_ers_movies_v2(db: Session) -> List[MovieSchemaV2]:
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

def get_movie_recommendation_text(db: Session, movie_id: uuid.UUID) -> Union[MovieRecommendationSchema, None]:
	db_response = db.query(MovieRecommendationText)\
		.filter(MovieRecommendationText.movie_id == movie_id)\
		.first()
	
	if db_response is None:
		return None

	# FIXME: This is a temporary fix and should updated in the database
	if db_response.source is None:
		db_response.source = ''
	if db_response.model is None:
		db_response.model = ''

	return MovieRecommendationSchema.model_validate(db_response)


def get_movie_by_exact_title_search(db: Session, title_query: str):
		# Exact Match Search (Case-insensitive)
	exact_match_result = db.query(Movie).filter(func.lower(Movie.title) == title_query).all()
	
	return exact_match_result


def get_movies_by_fuzzy_title_match(db: Session, title_query: str, similarity_threshold: float = 0.7, limit: int = 5):
	# Fuzzy Match Search using pg_trgm
	fuzzy_matches_results = db.query(Movie, func.similarity(Movie.title, title_query).label("similarity")) \
		.filter(func.similarity(Movie.title, title_query) > similarity_threshold) \
		.order_by(func.similarity(Movie.title, title_query).desc()) \
		.limit(limit) \
		.all()

	return fuzzy_matches_results


def get_movies_by_title_prefix_match(db: Session, title_query: str, limit: int = 5):
	# Prefix Match Search
	prefix_matches_results = db.query(Movie).filter(func.lower(Movie.title).like(f"{title_query}%")).limit(limit).all()

	return prefix_matches_results