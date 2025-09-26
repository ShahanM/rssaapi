from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from auth.security import get_auth0_authenticated_user, require_permissions
from data.schemas.movie_schemas import (
    ImdbReviewsPayloadSchema,
    MovieDetailSchema,
    MovieSchema,
    MovieSearchRequest,
    MovieSearchResponse,
    PaginatedMovieList,
)
from data.services import MovieService
from data.services.content_dependencies import get_movie_service
from docs.admin_docs import Tags

router = APIRouter(
    prefix='/movies',
    dependencies=[
        Depends(get_movie_service),
        Depends(get_auth0_authenticated_user),
        Depends(require_permissions('read:movies')),
    ],
    tags=[Tags.movie],
)


@router.get('/summary', response_model=list[MovieSchema])
async def get_movies(
    movie_service: Annotated[MovieService, Depends(get_movie_service)],
    offset: int = Query(0, ge=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies = await movie_service.get_movies(limit, offset)

    return [MovieSchema.model_validate(movie) for movie in movies]


@router.get('/', response_model=PaginatedMovieList)
async def get_movies_with_details(
    movie_service: Annotated[MovieService, Depends(get_movie_service)],
    offset: int = Query(0, ge=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies = await movie_service.get_movies_with_details(limit, offset)
    count = await movie_service.get_movie_count()

    validated_movies = [MovieDetailSchema.model_validate(movie) for movie in movies]
    response_obj = PaginatedMovieList(data=validated_movies, count=count)

    return response_obj


@router.post('/reviews', status_code=status.HTTP_201_CREATED)
async def create_movie_reviews(
    payload: ImdbReviewsPayloadSchema,
    movie_service: Annotated[MovieService, Depends(get_movie_service)],
):
    print(payload.imdb_id, len(payload.reviews))
    movie = await movie_service.get_movie_by_imdb_id(payload.imdb_id)
    if movie:
        print(MovieSchema.model_validate(movie))
    else:
        print('Could not find movie')

    return {'message': 'Reviews added to the movie.'}
