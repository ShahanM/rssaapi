from typing import List
from random import shuffle

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.utils import *
from data.models.schema.studyschema import *
from docs.metadata import TagsMetadataEnum as Tags

from data.moviedatabase import SessionLocal
from data.moviedb import get_db as movie_db_v2
from data.models.schema.movieschema import *
from data.movies import *

import uuid


router = APIRouter(prefix='/v2')


# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


@router.get(
	'/movie/ids/ers',
	response_model=List[uuid.UUID],
	tags=[Tags.ers])
async def read_movies_ids(db: Session = Depends(movie_db_v2)):
	''' Get all movie ids from the ERS database
		in v2, this endpoint returns the ids of all movies in the ERS database
		but they are randomly shuffled.
		So, each subsequent call will return a different order of ids.
	'''
	movies = get_all_ers_movies_v2(db)
	ids = [movie.id for movie in movies]
	shuffle(ids)
	return ids


# @router.get('/movies/ers', response_model=List[MovieSchema], \
# 	tags=['ers movie'])
# async def read_movies(skip: int = 0, limit: int = 100, \
# 	db: Session = Depends(get_db)):
# 	movies = get_ers_movies(db, skip=skip, limit=limit)
	
# 	return movies


@router.post(
	'/movie/ers',
	response_model=List[MovieSchemaV2],
	tags=[Tags.ers])
async def read_movies_by_ids(movie_ids: List[uuid.UUID], \
	db: Session = Depends(movie_db_v2)):
	movies = get_ers_movies_by_ids_v2(db, movie_ids)
	
	return movies


