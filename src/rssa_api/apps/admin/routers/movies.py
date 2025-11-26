from fastapi import APIRouter, Depends, Query, status

from rssa_api.apps.admin.docs import ADMIN_MOVIES_TAG
from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas.movie_schemas import (
    ImdbReviewsPayloadSchema,
    MovieDetailSchema,
    MovieSchema,
    PaginatedMovieList,
)
from rssa_api.data.services import MovieServiceDep

router = APIRouter(
    prefix='/movies',
    dependencies=[
        Depends(get_auth0_authenticated_user),
        Depends(require_permissions('read:movies')),
    ],
    tags=[ADMIN_MOVIES_TAG],
)


@router.get('/summary', response_model=list[MovieSchema])
async def get_movies(
    movie_service: MovieServiceDep,
    offset: int = Query(0, ge=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies = await movie_service.get_movies(limit, offset)

    return [MovieSchema.model_validate(movie) for movie in movies]


@router.get('/', response_model=PaginatedMovieList)
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


@router.post('/reviews', status_code=status.HTTP_201_CREATED)
async def create_movie_reviews(
    payload: ImdbReviewsPayloadSchema,
    movie_service: MovieServiceDep,
):
    print(payload.imdb_id, len(payload.reviews))
    movie = await movie_service.get_movie_by_imdb_id(payload.imdb_id)
    if movie:
        print(MovieSchema.model_validate(movie))
    else:
        print('Could not find movie')

    return {'message': 'Reviews added to the movie.'}
