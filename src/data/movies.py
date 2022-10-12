from sqlalchemy.orm import Session
from .models.movie import Movie
from typing import List

def get_movies(db: Session, skip: int = 0, limit: int = 30) -> List[Movie]:
	return db.query(Movie).offset(skip).limit(limit).all()

def get_movie(db: Session, movie_id: int) -> Movie:
	return db.query(Movie).filter(Movie.id == movie_id).first()

def get_movies_by_ids(db: Session, movie_ids: List[int]) -> List[Movie]:
	return db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
