from sqlalchemy.orm import Session
from .models.movie import Movie
from typing import List
from .models.schema.movieschema import MovieSchema
from math import isnan


def sanitize_movie(movie: Movie) -> MovieSchema:
	movie_ = MovieSchema.from_orm(movie)
	if movie_.cast == None:
		movie_.cast = ''
	if movie_.ave_rating == None or isnan(movie_.ave_rating):
		movie_.ave_rating = 0

	return movie_


def get_movies(db: Session, skip: int = 0, limit: int = 30) -> List[MovieSchema]:
	movies = db.query(Movie).offset(skip).limit(limit).all()

	return [sanitize_movie(movie) for movie in movies]

def get_movie(db: Session, movie_id: int) -> Movie:
	movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
	if movie:
		return movie
	else:
		return Movie()

def get_movies_by_ids(db: Session, movie_ids: List[int]) -> List[Movie]:
	return db.query(Movie).filter(Movie.movie_id.in_(movie_ids)).all()  # type: ignore

def get_all_ers_movies(db: Session) -> List[Movie]:
	return db.query(Movie).filter(Movie.emotions != None).all()  # type: ignore

def get_ers_movies(db: Session, skip: int = 0, limit: int = 30) -> List[Movie]:
	return db.query(Movie).filter(Movie.emotions != None).offset(skip).limit(limit).all()  # type: ignore

def get_ers_movies_by_ids(db: Session, movie_ids: List[int]) -> List[MovieSchema]:
	movies = db.query(Movie).filter(Movie.movie_id.in_(movie_ids))\
		.filter(Movie.emotions != None).all()

	# Order movies to main recommendation order
	movie_dict = {movie.movie_id: movie for movie in movies}
	movies = [movie_dict[movie_id] for movie_id in movie_ids]
	return [sanitize_movie(movie) for movie in movies]


def get_ers_movie(db: Session, movie_id: int) -> Movie:
	movie = db.query(Movie).filter(Movie.movie_id == movie_id)\
		.filter(Movie.emotions != None).first()
	if movie:
		return movie
	else:
		return Movie()