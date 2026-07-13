import math
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from rssa_api.data.schemas.base_schemas import DBMixin, PaginatedResponse
from rssa_api.data.schemas.movie_schemas import (
    MovieGalleryPreview,
)
from rssa_api.data.services.dependencies import MovieServiceDep, PreShuffledMovieServiceDep

router = APIRouter(
    prefix='/movies',
    tags=['Movies'],
)


# @router.get('/', response_model=PaginatedResponse[MovieGalleryPreview])
# async def get_movies(
#     movie_service: MovieServiceDep,
#     offset: int = Query(0, get=0, description='The starting index of the movies to return'),
#     limit: int = Query(10, ge=1, le=100, description='The maximum number of movies to return'),
# ):
#     movies = await movie_service.get_all_cached(MovieGalleryPreview, limit=limit, offset=offset)
#     total_items = await movie_service.get_movie_count()
#     page_count = math.ceil(total_items / float(limit)) if total_items > 0 else 1
#     response_obj = PaginatedResponse[MovieGalleryPreview](data=movies, page_count=page_count, total=total_items)

#     return response_obj


@router.get('/', response_model=PaginatedResponse[MovieGalleryPreview])
async def get_movies(
    # list_id: uuid.UUID,
    movie_service: MovieServiceDep,
    shuffled_list_service: PreShuffledMovieServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    list_id = uuid.UUID('3e6e2719-ceba-4bdf-bf76-6aefef013be6')  # FIXME: this is a temporary hardcoded solution
    shuffled_list = await shuffled_list_service.get(list_id, DBMixin)
    if not shuffled_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='List not found')

    movie_ids, total = await shuffled_list_service.get_movie_ids(shuffled_list.id, offset, limit)

    movies = await movie_service.get_movies_from_ids(MovieGalleryPreview, movie_ids)
    page_count = math.ceil(total / limit) if total > 0 else 1

    return PaginatedResponse[MovieGalleryPreview](data=movies, page_count=page_count, total=total)
