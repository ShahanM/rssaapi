import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from data.schemas.movie_schemas import MovieSchema, MovieSearchRequest, MovieSearchResponse
from data.services import MovieService, ParticipantSessionService
from data.services.content_dependencies import get_movie_service
from data.services.rssa_dependencies import get_participant_session_service
from docs.metadata import ResourceTagsEnum as Tags
from routers.v2.resources.authorization import get_current_participant_id

router = APIRouter(
	prefix='/movies',
	tags=[Tags.movie],
)


@router.get('/ers', response_model=list[MovieSchema])
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


@router.post('/search', response_model=list[MovieSchema])
async def search_movie(
	request: MovieSearchRequest,
	movie_service: Annotated[MovieService, Depends(get_movie_service)],
):
	query = request.query.strip().lower()
	exact_match = []
	# near_matches: List[str] = []
	near_matches: list[MovieSchema] = []
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
