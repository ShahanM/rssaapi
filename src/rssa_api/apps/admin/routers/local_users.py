"""Router for managing local users in the admin API."""

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema, UserSchema
from rssa_api.data.schemas.base_schemas import SortDir
from rssa_api.data.services.dependencies import UserServiceDep

from ..docs import ADMIN_USERS_TAG

router = APIRouter(
    prefix='/local-users',
    tags=[ADMIN_USERS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


class PaginatedUserResponse(BaseModel):
    """Paginated response for users."""

    rows: list[UserSchema]
    page_count: int


@router.get(
    '/',
    response_model=PaginatedUserResponse,
    summary='Get a paginated and sortable list of local users',
    description="""
    Retrieves a paginated list of all the users in the local database.
    Supports sorting by a specific field.
    """,
    response_description='A paginated list of users with total page count',
)
async def get_local_users(
    service: UserServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: str | None = Query(None, description='The field to sort by.'),
    sort_dir: SortDir | None = Query(None, description='The direction to sort (asc or desc)'),
    search: str | None = Query(None, description='A search term to filter results'),
) -> PaginatedUserResponse:
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
    users_from_db = await service.get_paged_list(
        limit=page_size,
        offset=offset,
        schema=UserSchema,
        sort_by=sort_by,
        sort_dir=sort_dir.value if sort_dir else None,
        search=search,
    )
    page_count = math.ceil(total_items / float(page_size)) if total_items > 0 else 1

    return PaginatedUserResponse(rows=users_from_db, page_count=page_count)


@router.get(
    '/{user_id}',
    response_model=UserSchema,
    summary='Get a single instance of a user',
    description="""
    Retrieves a single instance of a user from the local database.
    """,
    response_description='A detailed user instance, or a HTTP 404 NOT FOUND.',
)
async def get_user_detail(
    user_id: uuid.UUID,
    service: UserServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
) -> UserSchema:
    """Get details of a user.

    Args:
        user_id: The UUID of the user.
        service: The user service.
        _: Auth check.

    Raises:
        HTTPException: If user is not found.

    Returns:
        The user details.
    """
    user = await service.get_detailed(user_id, schema=UserSchema)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with ID {user_id} not found.')

    return user
