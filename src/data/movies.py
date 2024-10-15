from sqlalchemy.orm import Session
from .models.movie import Movie as Movie_old
from .models.movies_v2 import Movie, MovieEmotions
from typing import List
from .models.schema.movieschema import MovieSchema, MovieSchemaV2
from math import isnan
import uuid


@DeprecationWarning
def sanitize_movie(movie: Movie_old) -> MovieSchema:
	movie_ = MovieSchema.from_orm(movie)
	if movie_.cast == None:
		movie_.cast = ''
	if movie_.ave_rating == None or isnan(movie_.ave_rating):
		movie_.ave_rating = 0

	return movie_


@DeprecationWarning
def get_movies(db: Session, skip: int = 0, limit: int = 30) -> List[MovieSchema]:
	movies = db.query(Movie_old).offset(skip).limit(limit).all()

	return [sanitize_movie(movie) for movie in movies]

def get_movie(db: Session, movie_id: int) -> Movie:
	movie = db.query(Movie_old).filter(Movie.movie_id == movie_id).first()
	if movie:
		return movie
	else:
		return Movie()

def get_movies_by_ids(db: Session, movie_ids: List[int]) -> List[Movie]:
	return db.query(Movie).filter(Movie.movie_id.in_(movie_ids)).all()  # type: ignore


@DeprecationWarning
def get_all_ers_movies(db: Session) -> List[Movie]:
	return db.query(Movie_old).filter(Movie.emotions != None).all()  # type: ignore


def get_all_ers_movies_v2(db: Session) -> List[Movie]:
	results = db.query(Movie, MovieEmotions)\
		.join(MovieEmotions, Movie.id == MovieEmotions.movie_id)\
		.all()
	
	return [result[0] for result in results]


@DeprecationWarning
def get_ers_movies(db: Session, skip: int = 0, limit: int = 30) -> List[Movie_old]:
	return db.query(Movie_old).filter(Movie.emotions != None).offset(skip).limit(limit).all()  # type: ignore


def get_ers_movies_v2(db: Session, skip: int = 0, limit: int = 30) -> List[Movie]:
	return db.query(Movie, MovieEmotions)\
		.join(MovieEmotions, Movie.id == MovieEmotions.movie_id)\
		.offset(skip).limit(limit).all()


@DeprecationWarning
def get_ers_movies_by_ids(db: Session, movie_ids: List[int]) -> List[MovieSchema]:
	movies = db.query(Movie_old).filter(Movie.movie_id.in_(movie_ids))\
		.filter(Movie.emotions != None).all()

	# Order movies to main recommendation order
	movie_dict = {movie.movie_id: movie for movie in movies}
	movies = [movie_dict[movie_id] for movie_id in movie_ids]
	return [sanitize_movie(movie) for movie in movies]


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


def get_ers_movies_by_movielens_ids(db: Session, movielens_ids: List[str]) -> List[Movie]:
	results = db.query(Movie, MovieEmotions)\
		.join(MovieEmotions, Movie.id == MovieEmotions.movie_id)\
		.filter(Movie.movielens_id.in_(movielens_ids))\
		.all()
	
	movies = [result[0] for result in results]
	# Order movies to the requested order
	movie_dict = {movie.movielens_id: movie for movie in movies}
	movies = [movie_dict[movielens_id] for movielens_id in movielens_ids]
	return movies


@DeprecationWarning
def get_ers_movie(db: Session, movie_id: int) -> Movie_old:
	movie = db.query(Movie_old).filter(Movie.movie_id == movie_id)\
		.filter(Movie.emotions != None).first()
	if movie:
		return movie
	else:
		return Movie_old()
	