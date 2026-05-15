"""Router for PreShuffled movie list."""

import math
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import DBMixin, PaginatedResponse, SortDir
from rssa_api.data.schemas.movie_schemas import MovieGalleryPreview
from rssa_api.data.schemas.study_components import ShuffledMovieList, ShuffledMovieListCreate, ShufflingMovieQuerySchema
from rssa_api.data.services.dependencies import MovieServiceDep, PreShuffledMovieServiceDep

logging = structlog.getLogger()

router = APIRouter(
    prefix='/shuffled-lists',
    include_in_schema=False,
    dependencies=[
        Depends(get_auth0_authenticated_user),
        Depends(require_permissions('admin:all')),
    ],
)


@router.get(
    '/',
    response_model=PaginatedResponse[ShuffledMovieList],
    summary='Get a paginated and sortable list of local users',
    description="""
    Retrieves a paginated list of all the users in the local database.
    Supports sorting by a specific field.
    """,
    response_description='A paginated list of users with total page count',
)
async def get_shuffled_lists(
    service: PreShuffledMovieServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: str | None = Query(None, description='The field to sort by.'),
    sort_dir: SortDir | None = Query(None, description='The direction to sort (asc or desc)'),
    search: str | None = Query(None, description='A search term to filter results'),
) -> PaginatedResponse[ShuffledMovieList]:
    """Get a paginated list of local users.

    Args:
        service: The user service.
        _: Auth check.
        page_index: The page number (0-indexed).
        page_size: Items per page.
        sort_by: Field to sort by.
        sort_dir: Sort direction.
        search: Search term.

    Returns:
        Paginated list of users.
    """
    offset = page_index * page_size
    total_items = await service.count(search=search)
    lists_from_db = await service.get_all(
        ShuffledMovieList,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sort_dir.value if sort_dir else None,
        search=search,
    )
    page_count = math.ceil(total_items / float(page_size)) if total_items > 0 else 1

    return PaginatedResponse[ShuffledMovieList](data=lists_from_db, page_count=page_count, total=total_items)


SHUFFLING_STRATEGY = ['A-Res', 'Stratified Chunking', 'Random']


@router.post('/')
async def create_new_shuffled_list(
    payload: ShuffledMovieListCreate,
    shuffled_service: PreShuffledMovieServiceDep,
    movie_service: MovieServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
):
    """Creates a new randomized sequence of movies based on filter criteria."""
    query_opts = movie_service.get_filter_opts(
        genre=payload.genre,
        year_min=payload.year_min,
        year_max=payload.year_max,
        exclude_no_emotions=payload.exclude_no_emotions,
        exclude_no_recommendations=payload.exclude_no_recommendations,
    )

    query_opts.filter_ranges.append(('movielens_rate_count', '>=', payload.min_rate_count))
    query_opts.filter_not_null.append('tmdb_poster')

    strategy = payload.strategy
    movies = await movie_service.get_all(
        ShufflingMovieQuerySchema,
        options=query_opts,
    )

    if not movies:
        raise HTTPException(status_code=400, detail='No movies matched the given criteria. Try relaxing your filters.')

    if strategy == 'A-Res':
        movie_data = [{'id': movie.id, 'weight': math.log10(movie.rate_count + 1)} for movie in movies]
    elif 'Stratified Chunking' in strategy:
        movie_data = [
            {
                'id': movie.id,
                'rate_count': movie.rate_count,
                'average_rating': movie.avg_rating,
            }
            for movie in movies
        ]
    else:
        movie_data = [{'id': movie.id} for movie in movies]

    config_payload = payload.model_dump(exclude={'seeds', 'subset_desc'})
    for current_seed in payload.seeds:
        logging.info('Generating shuffled movie list', seed=current_seed, strategy=strategy)
        await shuffled_service.create_pre_shuffled_movie_list(
            movie_data=movie_data,
            subset_desc=payload.subset_desc,
            seed=current_seed,
            config_payload=config_payload,
        )

    return {
        'status': 'success',
        'message': f"Successfully created shuffled list '{payload.subset_desc}' with {len(movie_data)} movies.",
    }


@router.get(
    '/{list_id}/movies',
    response_model=PaginatedResponse[MovieGalleryPreview],
    summary='Get paginated movies for a specific shuffled list',
)
async def get_shuffled_list_movies(
    list_id: uuid.UUID,
    movie_service: MovieServiceDep,
    shuffled_list_service: PreShuffledMovieServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    shuffled_list = await shuffled_list_service.get(list_id, DBMixin)
    if not shuffled_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='List not found')

    movie_ids, total = await shuffled_list_service.get_movie_ids(shuffled_list.id, offset, limit)

    movies = await movie_service.get_movies_from_ids(MovieGalleryPreview, movie_ids)
    page_count = math.ceil(total / limit) if total > 0 else 1

    return PaginatedResponse[MovieGalleryPreview](data=movies, page_count=page_count, total=total)


@router.delete('/{list_id}', status_code=status.HTTP_204_NO_CONTENT, summary='Delete a pre-shuffled movie list')
async def delete_shuffled_list(
    list_id: uuid.UUID,
    shuffled_list_service: PreShuffledMovieServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
):
    """Delete a shuffled list and its associated array."""
    existing_list = await shuffled_list_service.get(list_id, DBMixin)
    if not existing_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='List not found.')

    await shuffled_list_service.delete(list_id)
