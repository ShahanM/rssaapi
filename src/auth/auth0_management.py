# in a file like 'core/auth0_management.py'
from typing import Optional

import httpx
from async_lru import alru_cache
from fastapi import HTTPException, status

from core.config import (
    AUTH0_API_AUDIENCE,
    AUTH0_CLIENT_ID,
    AUTH0_CLIENT_SECRET,
    AUTH0_DOMAIN,
    AUTH0_MANAGEMENT_API_AUDIENCE,
    RESOURCE_SERVER_URL,
)


@alru_cache(ttl=3600)
async def get_management_api_token() -> str:
    """Fetches and caches the Auth0 Management API token."""
    url = f'https://{AUTH0_DOMAIN}/oauth/token'
    payload = {
        'client_id': AUTH0_CLIENT_ID,
        'client_secret': AUTH0_CLIENT_SECRET,
        'audience': AUTH0_MANAGEMENT_API_AUDIENCE,
        'grant_type': 'client_credentials',
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            token = response.json().get('access_token')
            if not token:
                raise HTTPException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR, 'Auth0: Failed to obtain management API token.'
                )
            return token
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                e.response.status_code, f'Auth0: HTTP error obtaining management API token: {e.response.text}'
            ) from e


async def get_resource_server_scopes() -> list[dict]:
    """Retrieves all defined scopes for the Auth0 API (Resource Server)."""
    token = await get_management_api_token()
    headers = {'Authorization': f'Bearer {token}'}
    async with httpx.AsyncClient(headers=headers) as client:
        try:
            response = await client.get(RESOURCE_SERVER_URL)
            response.raise_for_status()
            return response.json().get('scopes', [])
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                e.response.status_code, f'Auth0: HTTP error getting resource server scopes: {e.response.text}'
            ) from e


def get_management_api_authorized_client(token: str) -> httpx.AsyncClient:
    """Returns an httpx.AsyncClient configured with the management API token.

    Args:
            token (str): _description_

    Returns:
            httpx.AsyncClient: _description_
    """
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
    client = httpx.AsyncClient(headers=headers)
    return client


async def create_permission_scope(permission_name: str, permission_description: str) -> list[dict]:
    """Creates a new permission scope for the AUth0 API

    Args:
            permission_name (str): _description_
            permission_description (str): _description_

    Raises:
            HTTPException: _description_
            HTTPException: _description_

    Returns:
            List[dict]: _description_
    """
    token = await get_management_api_token()
    current_scopes = await get_resource_server_scopes()
    client = get_management_api_authorized_client(token)

    new_scope_obj = {
        'value': permission_name,
        'description': permission_description,
    }

    if any(scope['value'] == permission_name for scope in current_scopes):
        print(f'Permission scope "{permission_name}" already exists. Skipping creation.')
        return current_scopes

    udpated_scopes = current_scopes + [new_scope_obj]
    payload = {'scopes': udpated_scopes}

    async with client:
        try:
            response = await client.patch(RESOURCE_SERVER_URL, json=payload)
            response.raise_for_status()
            response_json = response.json()
            return response_json.get('scopes', [])
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f'Auth0: HTTP error creating permission scope: {e.response.text}',
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Auth0: Unexpected error creating permission scope: {e}',
            ) from e


async def delete_permission_scope(permission_name: str) -> list[dict]:
    """Deletes a permission scope from the AUth0 API

    Args:
            permission_name (str): _description_

    Raises:
            HTTPException: _description_
            HTTPException: _description_

    Returns:
            List[dict]: _description_
    """
    token = await get_management_api_token()
    current_scopes = await get_resource_server_scopes()
    client = get_management_api_authorized_client(token)

    updated_scopes = [scope for scope in current_scopes if scope['value'] != permission_name]
    payload = {'scopes': updated_scopes}

    async with client:
        try:
            response = await client.patch(RESOURCE_SERVER_URL, json=payload)
            response.raise_for_status()
            response_json = response.json()
            return response_json.get('scopes', [])
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f'Auth0: HTTP error deleting permission scope: {e.response.text}',
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Auth0: Unexpected error deleting permission scope: {e}',
            ) from e


async def assign_permission_to_user(user_id: str, permission_name: str):
    """Assigns a permission to a specific Auth0 user.

    Args:
            user_id (str): _description_
            permission_name (str): _description_

    Raises:
            HTTPException: _description_
            HTTPException: _description_
            HTTPException: _description_
            HTTPException: _description_
            HTTPException: _description_

    Returns:
            _type_: _description_
    """
    token = await get_management_api_token()
    url = f'https://{AUTH0_DOMAIN}/api/v2/users/{user_id}/permissions'
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}
    payload = {
        'permissions': [
            {
                'permission_name': permission_name,
                'resource_server_identifier': AUTH0_API_AUDIENCE,
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return {'message': f'Permission "{permission_name}" assigned to use "{user_id}"'}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Auth0: Invalid client credentials for management API.',
                ) from e
            elif e.response.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'Auth0: User {user_id} not found or permission not found.',
                ) from e
            elif e.response.status_code == status.HTTP_409_CONFLICT:  # Auth0 returns 409 if permission already assigned
                return {'message': f"Permission '{permission_name}' already assigned to user o'{user_id}'"}
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f'Auth0: HTTP error assigning permission: {e.response.text}',
                ) from e
        except httpx.ConnectTimeout as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'Auth0: Connection timeout assigning permission: {e}',
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Auth0: Unexpected error assigning permission: {e}',
            ) from e


async def get_user_profile_by_id(user_id: str) -> Optional[dict]:
    """
    Fetches a user's public profile (name, picture) from the Auth0 Management API.
    """
    print('Getting user profile for', user_id)
    token = await get_management_api_token()
    print('I GOT MY TOKEN')
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://{AUTH0_DOMAIN}/api/v2/users/{user_id}'

    async with httpx.AsyncClient(headers=headers) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

            user_data = response.json()

            return {
                'name': user_data.get('name'),
                'picture': user_data.get('picture'),
                'nickname': user_data.get('nickname'),
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f'Auth0: HTTP error getting user profile: {e.response.text}',
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Auth0: Unexpected error getting user profile: {e}',
            ) from e


async def search_users(search_query: Optional[str] = None, page: int = 0, per_page: int = 50) -> list[dict]:
    """
    Searches for users in Auth0, with pagination.
    Returns a list of user profiles containing only essential fields.
    """
    token = await get_management_api_token()
    headers = {'Authorization': f'Bearer {token}'}

    fields_to_include = 'user_id,name,email,picture,nickname'

    params = {
        'per_page': per_page,
        'page': page,
        'include_fields': 'true',
        'fields': fields_to_include,
        'search_engine': 'v3',
    }

    if search_query:
        params['q'] = search_query

    url = f'https://{AUTH0_DOMAIN}/api/v2/users'

    async with httpx.AsyncClient(headers=headers) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f'Auth0: HTTP error searching users: {e.response.text}',
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Auth0: Unexpected error searching users: {e}',
            ) from e
