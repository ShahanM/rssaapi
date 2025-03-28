from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import List

from data.moviedatabase import SessionLocal
from data.models.schemas.movieschema import *
from data.movies import *
from docs.metadata import TagsMetadataEnum as Tags


router = APIRouter(prefix='/v1', deprecated=True)


# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

@router.get(
		'/ers/movies/ids/',
		response_model=List[int],
		tags=[Tags.ers],
		deprecated=True)
async def read_movies_ids_dep(db: Session = Depends(get_db)):
	movies = get_all_ers_movies(db)
	ids = [movie.movie_id for movie in movies]
	return ids


@router.get(
		'/ers/movies/',
		response_model=List[MovieSchema],
		tags=[Tags.ers],
		deprecated=True)
async def read_movies_dep(skip: int = 0, limit: int = 100, \
	db: Session = Depends(get_db)):
	movies = get_ers_movies(db, skip=skip, limit=limit)
	
	return movies


@router.post(
		'/ers/movies/',
		response_model=List[MovieSchema],
		tags=[Tags.ers],
		deprecated=True)
async def read_movies_by_ids_dep(movie_ids: List[int], \
	db: Session = Depends(get_db)):
	movies = get_ers_movies_by_ids(db, movie_ids)
	
	return movies