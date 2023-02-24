from sqlalchemy.orm import Session
from .models.movie import Movie
from typing import List

def get_movies(db: Session, skip: int = 0, limit: int = 30) -> List[Movie]:
	return db.query(Movie).offset(skip).limit(limit).all()

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

def get_ers_movies_by_ids(db: Session, movie_ids: List[int]) -> List[Movie]:
	movies = db.query(Movie).filter(Movie.movie_id.in_(movie_ids))\
		.filter(Movie.emotions != None).all()
	for movie in movies:
		if movie.cast == None:
			movie.cast = ''
		if movie.ave_rating == None:
			movie.ave_rating = 0
	return movies 