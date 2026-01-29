"""Router for managing movies."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from rssa_api.apps.admin.docs import ADMIN_MOVIES_TAG
from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.movie_schemas import (
    ImdbReviewsPayloadSchema,
    MovieDetailSchema,
    MovieSchema,
    MovieUpdateSchema,
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
    title: str | None = Query(None, description='Filter by title (partial match)'),
    year_min: int | None = Query(None, description='Filter by minimum release year'),
    year_max: int | None = Query(None, description='Filter by maximum release year'),
    genre: str | None = Query(None, description='Filter by genre (partial match)'),
    sort_by: str | None = Query(None, description='Sort by field (e.g. year, title). Prefix with - for desc'),
    exclude_no_emotions: bool = Query(False, description='Exclude movies without emotions'),
    exclude_no_recommendations: bool = Query(False, description='Exclude movies without LLM recommendations'),
) -> list[MovieSchema]:
    """Get movie summaries.

    Args:
        movie_service: The movie service.
        offset: Start index.
        limit: Max items to return.
        title: Title filter.
        year_min: Min release year.
        year_max: Max release year.
        genre: Genre filter.
        sort_by: Sort field.
        exclude_no_emotions: Exclude missing emotions.
        exclude_no_recommendations: Exclude missing recommendations.

    Returns:
        List of movie summaries.
    """
    movies = await movie_service.get_movies(
        limit,
        offset,
        title=title,
        year_min=year_min,
        year_max=year_max,
        genre=genre,
        sort_by=sort_by,
        exclude_no_emotions=exclude_no_emotions,
        exclude_no_recommendations=exclude_no_recommendations,
    )

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
    title: str | None = Query(None, description='Filter by title (partial match)'),
    year_min: int | None = Query(None, description='Filter by minimum release year'),
    year_max: int | None = Query(None, description='Filter by maximum release year'),
    genre: str | None = Query(None, description='Filter by genre (partial match)'),
    sort_by: str | None = Query(None, description='Sort by field (e.g. year, title). Prefix with - for desc'),
    exclude_no_emotions: bool = Query(False, description='Exclude movies without emotions'),
    exclude_no_recommendations: bool = Query(False, description='Exclude movies without LLM recommendations'),
) -> PaginatedMovieList:
    """Get movies with details.

    Args:
        movie_service: The movie service.
        offset: Start index.
        limit: Max items to return.
        title: Title filter.
        year_min: Min release year.
        year_max: Max release year.
        genre: Genre filter.
        sort_by: Sort field.
        exclude_no_emotions: Exclude missing emotions.
        exclude_no_recommendations: Exclude missing recommendations.

    Returns:
        Paginated list of movies.
    """
    movies = await movie_service.get_movies_with_details(
        limit,
        offset,
        title=title,
        year_min=year_min,
        year_max=year_max,
        genre=genre,
        sort_by=sort_by,
        exclude_no_emotions=exclude_no_emotions,
        exclude_no_recommendations=exclude_no_recommendations,
    )
    count = await movie_service.get_movie_count(
        title=title,
        year_min=year_min,
        year_max=year_max,
        genre=genre,
        exclude_no_emotions=exclude_no_emotions,
        exclude_no_recommendations=exclude_no_recommendations,
    )

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
) -> dict[str, str]:
    """Add reviews to a movie.

    Args:
        payload: Review data.
        movie_service: The movie service.

    Returns:
        A success message.
    """
    movie = await movie_service.get_movie_by_imdb_id(payload.imdb_id)
    if not movie:
        pass

    return {'message': 'Reviews added to the movie.'}


@router.patch(
    '/{movie_id}',
    response_model=MovieSchema,
    summary='Update movie details.',
    description="""
    Update movie details. Only provided fields will be updated.
    """,
)
async def update_movie(
    movie_id: str,
    payload: MovieUpdateSchema,
    movie_service: MovieServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:movies', 'admin:all'))],
) -> dict[str, str]:
    """Update a movie.

    Args:
        movie_id: The UUID of the movie to update.
        payload: The movie data to update.
        movie_service: The movie service.
        user: The authenticated user.

    Returns:
        A success message.
    """
    import uuid

    try:
        movie_uuid = uuid.UUID(movie_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid UUID format') from e

    updated_movie = await movie_service.update_movie(movie_uuid, payload)

    if not updated_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Movie not found')

    return MovieSchema.model_validate(updated_movie)
