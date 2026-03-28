"""Router for PreShuffled movie list."""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import SortDir
from rssa_api.data.services.dependencies import MovieServiceDep, PreShuffledMovieServiceDep

router = APIRouter(
    prefix='/shuffled-lists',
    dependencies=[
        Depends(get_auth0_authenticated_user),
        Depends(require_permissions('admin:all')),
    ],
)


class ShuffledMovieListCreate(BaseModel):
    """Payload for generating a new pre-shuffled subset of movies."""

    subset_desc: str
    seed: int = 144

    # Optional Filtering Criteria
    # year_min: int | None = None
    # year_max: int | None = None
    # genre: str | None = None
    exclude_no_emotions: bool = False
    exclude_no_recommendations: bool = False


class ShuffledMovieList(BaseModel):
    """ShhuffledMovieList schema."""

    subset_desc: str
    seed: int

    model_config = ConfigDict(from_attributes=True)


class PaginatedListResponse(BaseModel):
    """Paginated response for users."""

    rows: list[ShuffledMovieList]
    page_count: int


@router.get(
    '/',
    response_model=PaginatedListResponse,
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
) -> ShuffledMovieList:
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

    return PaginatedListResponse(rows=lists_from_db, page_count=page_count)


@router.post('/')
async def create_new_shuffled_list(
    payload: ShuffledMovieListCreate,
    shuffled_service: PreShuffledMovieServiceDep,
    movie_service: MovieServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
):
    """Creates a new randomized sequence of movies based on filter criteria."""
    movie_ids = await movie_service.get_filtered_movie_ids(
        # year_min=payload.year_min,
        # year_max=payload.year_max,
        # genre=payload.genre,
        exclude_no_emotions=payload.exclude_no_emotions,
        exclude_no_recommendations=payload.exclude_no_recommendations,
    )

    if not movie_ids:
        raise HTTPException(status_code=400, detail='No movies matched the given criteria. Try relaxing your filters.')

    await shuffled_service.create_pre_shuffled_movie_list(
        movie_ids=movie_ids, subset=payload.subset_desc, seed=payload.seed
    )

    return {
        'status': 'success',
        'message': f"Successfully created shuffled list '{payload.subset_desc}' with {len(movie_ids)} movies.",
    }
