import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from rssa_api.auth.authorization import get_current_participant, validate_study_participant
from rssa_api.data.schemas.movie_schemas import (
    MovieSchema,
    MovieSearchRequest,
    MovieSearchResponse,
    PaginatedMovieList,
)
from rssa_api.data.schemas.participant_schemas import StudyParticipantRead
from rssa_api.data.services.dependencies import MovieServiceDep, StudyParticipantMovieSessionServiceDep

router = APIRouter(
    prefix='/movies',
    tags=['Movies'],
)


@router.get('/ers', response_model=list[MovieSchema])
async def get_movies_with_emotions(
    movie_service: MovieServiceDep,
    session_service: StudyParticipantMovieSessionServiceDep,
    current_participant: Annotated[StudyParticipantRead, Depends(get_current_participant)],
    offset: int = Query(0, get=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies_to_fetch = await session_service.get_next_session_movie_ids_batch(current_participant.id, offset, limit)
    if movies_to_fetch:
        movies = await movie_service.get_movies_with_emotions_from_ids(movies_to_fetch.movies)
        if movies:
            movies_to_send = [MovieSchema.model_validate(m) for m in movies]
            return movies_to_send


@router.get('/', response_model=PaginatedMovieList)
async def get_movies(
    movie_service: MovieServiceDep,
    session_service: StudyParticipantMovieSessionServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
    offset: int = Query(0, get=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies_to_fetch = await session_service.get_next_session_movie_ids_batch(id_token['pid'], offset, limit)
    if movies_to_fetch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Could not find a valid session.')
    movies = await movie_service.get_movies_from_ids(movies_to_fetch.movies)
    response_obj = PaginatedMovieList(data=movies, count=movies_to_fetch.total)

    return response_obj


@router.post('/search', response_model=list[MovieSchema])
async def search_movie(
    request: MovieSearchRequest,
    movie_service: MovieServiceDep,
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
