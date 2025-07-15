import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from data.schemas.movie_schemas import MovieSchema, MovieSearchRequest, MovieSearchResponse
from data.services import MovieService, ParticipantSessionService
from data.services.content_dependencies import get_movie_service
from data.services.rssa_dependencies import get_participant_session_service
from docs.metadata import ResourceTagsEnum as Tags
from routers.v2.resources.authorization import get_current_participant_id

router = APIRouter(
	prefix='/v2/movies',
	tags=[Tags.movie],
)


# Dependency
# def get_db():
# 	db = SessionLocal()
# 	try:
# 		yield db
# 	finally:
# 		db.close()


@router.get('/ers', response_model=List[MovieSchema])
async def get_movies_with_emotions(
	movie_service: Annotated[MovieService, Depends(get_movie_service)],
	session_service: Annotated[ParticipantSessionService, Depends(get_participant_session_service)],
	current_participant_id: Annotated[uuid.UUID, Depends(get_current_participant_id)],
	offset: int = Query(0, get=0, description='The starting index of the movies to return'),
	limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
	movies_to_fetch = await session_service.get_next_session_movie_ids_batch(current_participant_id, offset, limit)
	if movies_to_fetch:
		movies = await movie_service.get_movies_with_emotions_from_ids(list(movies_to_fetch))
		if movies:
			movies_to_send = [MovieSchema.model_validate(m) for m in movies]
			return movies_to_send


# @router.get('/ids/ers', response_model=List[uuid.UUID], tags=[Tags.ers])
# async def read_movies_ids(db: AsyncSession = Depends(movie_db)):
# 	"""Get all movie ids from the ERS database
# 	in v2, this endpoint returns the ids of all movies in the ERS database
# 	but they are randomly shuffled.
# 	So, each subsequent call will return a different order of ids.
# 	"""
# 	movies = get_all_ers_movies_v2(db)
# 	ids = [movie.id for movie in movies]
# 	shuffle(ids)
# 	return ids


# @router.get('/movies/ers', response_model=List[MovieSchema], \
# 	tags=['ers movie'])
# async def read_movies(skip: int = 0, limit: int = 100, \
# 	db: Session = Depends(get_db)):
# 	movies = get_ers_movies(db, skip=skip, limit=limit)

# 	return movies


# @router.post('/ers', response_model=List[MovieSchema])
# async def read_movies_by_ids(movie_ids: List[uuid.UUID], db: AsyncSession = Depends(movie_db)):
# 	movies = get_ers_movies_by_ids_v2(db, movie_ids)

# 	return movies


@router.post('/search', response_model=List[MovieSchema])
async def search_movie(
	request: MovieSearchRequest,
	movie_service: Annotated[MovieService, Depends(get_movie_service)],
):
	query = request.query.strip().lower()
	exact_match = []
	# near_matches: List[str] = []
	near_matches: List[MovieSchema] = []
	similarity_threshold = 0.6  # Adjust as needed
	limit = 5

	if not query:
		return MovieSearchResponse()
	exact_match_result = await movie_service.get_movie_by_exact_title_search(query)

	if exact_match_result:
		exact_match = [MovieSchema.model_validate(movie) for movie in exact_match_result]
		return exact_match

	fuzzy_matches_results = await movie_service.get_movies_by_fuzzy_title_match(query, similarity_threshold, limit)

	near_matches = [MovieSchema.model_validate(match) for match in fuzzy_matches_results]

	prefix_matches_results = await movie_service.get_movies_by_title_prefix_match(query, limit)
	prefix_matches = [MovieSchema.model_validate(match) for match in prefix_matches_results]

	if prefix_matches:
		near_matches = prefix_matches + near_matches

	# return MovieSearchResponse(exact_match=exact_match, near_matches=near_matches)
	return near_matches
