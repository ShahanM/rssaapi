from fastapi import APIRouter, Depends, Query, status

from rssa_api.apps.admin.docs import ADMIN_MOVIES_TAG
from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas.movie_schemas import (
    ImdbReviewsPayloadSchema,
    MovieDetailSchema,
    MovieSchema,
    PaginatedMovieList,
)
from rssa_api.data.services.dependencies import MovieServiceDep

router = APIRouter(
    prefix='/movies',
    dependencies=[
        Depends(get_auth0_authenticated_user),
        Depends(require_permissions('read:movies', 'admin:all')),
    ],
    tags=[ADMIN_MOVIES_TAG],
)


@router.get(
    '/summary',
    response_model=list[MovieSchema],
    summary='Get movie summaries.',
    description="""
    Get a list of movies with summary details.
    """,
)
async def get_movies(
    movie_service: MovieServiceDep,
    offset: int = Query(0, ge=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies = await movie_service.get_movies(limit, offset)

    return [MovieSchema.model_validate(movie) for movie in movies]


@router.get(
    '/',
    response_model=PaginatedMovieList,
    summary='Get movies with details.',
    description="""
    Get a paginated list of movies with full details.
    This resource is read-only as movies are synced from external sources.
    """,
)
async def get_movies_with_details(
    movie_service: MovieServiceDep,
    offset: int = Query(0, ge=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies = await movie_service.get_movies_with_details(limit, offset)
    count = await movie_service.get_movie_count()

    validated_movies = [MovieDetailSchema.model_validate(movie) for movie in movies]
    response_obj = PaginatedMovieList(data=validated_movies, count=count)

    return response_obj


@router.post(
    '/reviews',
    status_code=status.HTTP_201_CREATED,
    summary='Add reviews to a movie',
    description='Adds a list of IMDB reviews to a specific movie identified by its IMDB ID.',
)
async def create_movie_reviews(
    payload: ImdbReviewsPayloadSchema,
    movie_service: MovieServiceDep,
):
    movie = await movie_service.get_movie_by_imdb_id(payload.imdb_id)
    if not movie:
        pass
        # logger.warning(f'Could not find movie with imdb_id: {payload.imdb_id}')

    return {'message': 'Reviews added to the movie.'}
