from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from rssa_api.data.schemas.movie_schemas import (
    MovieDetailSchema,
    MovieSchema,
    MovieSearchRequest,
    MovieSearchResponse,
    PaginatedMovieList,
)
from rssa_api.data.services import MovieServiceDep
from rssa_api.data.utility import sa_obj_to_dict

router = APIRouter(
    prefix='/movies',
    tags=['Movies'],
)


@router.get('/', response_model=PaginatedMovieList)
async def get_movies(
    movie_service: MovieServiceDep,
    offset: int = Query(0, get=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies = await movie_service.get_movies(limit, offset, '')
    total_count = await movie_service.get_movie_count()
    validated_movies = []
    for movie in movies:
        movie_dict = sa_obj_to_dict(movie)
        movie_dict['emotions'] = None
        movie_dict['recommendations_text'] = None
        validated_movies.append(MovieDetailSchema.model_validate(movie_dict))

    # validated_movies = [MovieDetailSchema.model_validate(movie) for movie in movies]
    response_obj = PaginatedMovieList(data=validated_movies, count=total_count)

    return response_obj
