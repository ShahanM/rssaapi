"""Router for managing users in the admin API."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from rssa_api.auth.auth0_management import get_user_profile_by_id, search_users
from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema, UserSchema
from rssa_api.data.services.dependencies import UserServiceDep

from ..docs import ADMIN_USERS_TAG

router = APIRouter(
    prefix='/users',
    tags=[ADMIN_USERS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get(
    '/me',
    summary='Get current user.',
    response_model=UserSchema,
)
async def get_current_user_endpoint(
    db_user: Annotated[UserSchema, Depends(get_current_user)],
) -> UserSchema:
    """Get the currently authenticated user from local DB."""
    return db_user


@router.get(
    '/search',
    response_model=list[UserSchema],
    summary='Search local users.',
    description="""
    Search for users in the local database by email or name.
    """,
)
async def search_local_users(
    user_service: UserServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
    q: str = '',
) -> list[UserSchema]:
    """Search local users."""
    if not q:
        return []
    return [UserSchema.model_validate(u) for u in await user_service.search_users(q)]


@router.get('/{user_id}/profile')
async def get_user_profile_endpoint(
    user_id: str,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    user_service: UserServiceDep,
) -> dict[str, Any]:
    """API endpoint to fetch a user's public profile information and sync to local DB."""
    try:
        current_db_user = await user_service.get_user_by_auth0_sub(user.sub)
        if not current_db_user:
            await user_service.create_user_from_auth0(user)
        else:
            await user_service.update_user_from_auth0(current_db_user, user)
    except Exception:
        pass

    target_auth0_id = ''
    try:
        user_uuid = UUID(user_id)
        local_target_user = await user_service.get_user_by_id(user_uuid)
        if local_target_user:
            target_auth0_id = local_target_user.auth0_sub
        else:
            raise HTTPException(status_code=404, detail='User not found.')
    except ValueError as e:
        raise HTTPException(status_code=400, detail='Invalid User ID format. UUID required.') from e

    profile = await get_user_profile_by_id(target_auth0_id)
    if not profile:
        raise HTTPException(status_code=404, detail='User profile not found.')

    # We sync the Auth0 profile to the local DB for some granualar permissions.
    try:
        db_target_user = await user_service.get_user_by_auth0_sub(target_auth0_id)
        if db_target_user:
            name = profile.get('name') or profile.get('nickname')
            picture = profile.get('picture')
            email = profile.get('email')

            partial_user_schema = Auth0UserSchema(
                sub=target_auth0_id,
                name=name,
                picture=picture,
                email=email,
            )

            await user_service.update_user_from_auth0(db_target_user, partial_user_schema)

    except Exception:
        pass

    return profile


@router.get('/{user_id}/permissions')
async def get_user_permissions(
    user_id: str,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    admin: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
) -> dict[str, list[str]]:
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
) -> dict[str, Any]:
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
