from typing import List
from random import shuffle

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.utils import *
from data.models.schemas.studyschema import *
from docs.metadata import TagsMetadataEnum as Tags

# from data.moviedatabase import SessionLocal
from data.moviedb import get_db as movie_db_v2
from data.models.schemas.movieschema import *
# from data.movies import *
from data.accessors.movies import *

import uuid


router = APIRouter(prefix='/v2/movie')


# Dependency
# def get_db():
# 	db = SessionLocal()
# 	try:
# 		yield db
# 	finally:
# 		db.close()
class MovieSearchRequest(BaseModel):
	query: str

class MovieSearchResponse(BaseModel):
	exact_match: List[MovieSchemaV2] = []
	near_matches: List[MovieSchemaV2] = []


@router.get(
	'/ids/ers',
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
	'/ers',
	response_model=List[MovieSchemaV2],
	tags=[Tags.ers])
async def read_movies_by_ids(movie_ids: List[uuid.UUID], \
	db: Session = Depends(movie_db_v2)):
	movies = get_ers_movies_by_ids_v2(db, movie_ids)
	
	return movies


@router.post("/search_movie", response_model=List[MovieSchemaV2])
async def search_movie(request: MovieSearchRequest, db: Session = Depends(movie_db_v2)):
	query = request.query.strip().lower()
	exact_match = []
	# near_matches: List[str] = []
	near_matches: List[MovieSchemaV2] = []
	similarity_threshold = 0.6  # Adjust as needed
	limit = 5

	if not query:
		return MovieSearchResponse()

	exact_match_result = get_movie_by_exact_title_search(db, query)
	if exact_match_result:
		# exact_match = exact_match_result[0]
		exact_match = [MovieSchemaV2.model_validate(movie) for movie in exact_match_result]
		return exact_match
		# return MovieSearchResponse(exact_match=exact_match)
		# return MovieSearchResponse(exact_match=exact_match_result)

	fuzzy_matches_results = get_movies_by_fuzzy_title_match(db, query, similarity_threshold, limit)
	# near_matches = [match[0] for match in fuzzy_matches_results]
	near_matches = [match[0] for match in fuzzy_matches_results]

	prefix_matches_results = get_movies_by_title_prefix_match(db, query, limit)
	prefix_matches = [match for match in prefix_matches_results]


	if prefix_matches:
		# near_matches = near_matches + prefix_matches
		near_matches = prefix_matches + near_matches

	# return MovieSearchResponse(exact_match=exact_match, near_matches=near_matches)
	return near_matches