import math

from fastapi import APIRouter, Query

from rssa_api.data.schemas.base_schemas import PaginatedResponse
from rssa_api.data.schemas.movie_schemas import (
    MovieGalleryPreview,
)
from rssa_api.data.services.dependencies import MovieServiceDep

router = APIRouter(
    prefix='/movies',
    tags=['Movies'],
)


@router.get('/', response_model=PaginatedResponse[MovieGalleryPreview])
async def get_movies(
    movie_service: MovieServiceDep,
    offset: int = Query(0, get=0, description='The starting index of the movies to return'),
    limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
):
    movies = await movie_service.get_all_cached(MovieGalleryPreview, limit=limit, offset=offset)
    total_items = await movie_service.get_movie_count()
    page_count = math.ceil(total_items / float(limit)) if total_items > 0 else 1
    response_obj = PaginatedResponse[MovieGalleryPreview](data=movies, page_count=page_count, total=total_items)

    return response_obj
