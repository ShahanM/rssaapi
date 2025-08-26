from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException

from .auth0 import (
	Auth0UserSchema,
	get_auth0_authenticated_user,
	get_user_profile_by_id,
	require_permissions,
	search_users,
)

router = APIRouter(
	prefix='/admin/users',
	dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get('/{user_id}/profile')
async def get_user_profile_endpoint(
	user_id: str,
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	"""
	API endpoint to fetch a user's public profile information.
	"""
	profile = await get_user_profile_by_id(user_id)
	print(await search_users())
	if not profile:
		raise HTTPException(status_code=404, detail='User profile not found.')
	return profile


@router.get('/{user_id}/permissions')
async def get_user_permissions(
	user_id: str,
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
	admin: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
):
	"""
	API endpoint to fetch a user's permissions.
	"""
	profile = await get_user_profile_by_id(user_id)
	if not profile:
		raise HTTPException(status_code=404, detail='User profile not found.')
	return {'permissions': profile.get('permissions', [])}


@router.get('/users')
async def search_users_endpoint(
	q: Optional[str] = None,
	page: int = 0,
	per_page: int = 20,
	user: Auth0UserSchema = Depends(require_permissions('read:users')),
):
	"""API endpoint for searching users to assign permissions or roles."""
	users = await search_users(search_query=q, page=page, per_page=per_page)
	return users
