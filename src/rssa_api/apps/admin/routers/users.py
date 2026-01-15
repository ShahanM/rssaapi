"""Router for managing users in the admin API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from rssa_api.auth.auth0_management import get_user_profile_by_id, search_users
from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema

from ..docs import ADMIN_USERS_TAG

router = APIRouter(
    prefix='/users',
    tags=[ADMIN_USERS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get('/{user_id}/profile')
async def get_user_profile_endpoint(
    user_id: str,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    """API endpoint to fetch a user's public profile information."""
    profile = await get_user_profile_by_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail='User profile not found.')
    return profile


@router.get('/{user_id}/permissions')
async def get_user_permissions(
    user_id: str,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    admin: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
):
    """API endpoint to fetch a user's permissions."""
    profile = await get_user_profile_by_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail='User profile not found.')
    return {'permissions': profile.get('permissions', [])}


@router.get(
    '/',
    summary='Search users.',
    description="""
    API endpoint for searching users to assign permissions or roles.
    """,
)
async def search_users_endpoint(
    q: str | None = None,
    page: int = 0,
    per_page: int = 20,
    user: Auth0UserSchema = Depends(require_permissions('read:users')),
):
    """Search for users in Auth0.

    Args:
        q: The search query string.
        page: The page number (0-indexed).
        per_page: The number of results per page.
        user: Auth check.

    Returns:
        A dictionary containing the search results.
    """
    users = await search_users(search_query=q, page=page, per_page=per_page)
    return users
