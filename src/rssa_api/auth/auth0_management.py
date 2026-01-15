from typing import Any

import httpx
from async_lru import alru_cache
from fastapi import HTTPException, status

import rssa_api.core.config as cfg


async def _handle_auth0_request(
    client: httpx.AsyncClient, method: str, url: str, operation_name: str, **kwargs: Any
) -> Any:
    """Helper to execute Auth0 requests with standardized error handling."""
    try:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return None
        return response.json()
    except httpx.HTTPStatusError as e:
        detail = f'Auth0: HTTP error {operation_name}: {e.response.text}'
        raise HTTPException(status_code=e.response.status_code, detail=detail) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Auth0: Unexpected error {operation_name}: {e}',
        ) from e


@alru_cache(ttl=3600)
async def get_management_api_token() -> str:
    """Fetches and caches the Auth0 Management API token.

    Returns:
        str: The access token for the Management API.

    Raises:
        HTTPException: If the token cannot be obtained.
    """
    url = f'https://{cfg.AUTH0_DOMAIN}/oauth/token'
    payload = {
        'client_id': cfg.AUTH0_CLIENT_ID,
        'client_secret': cfg.AUTH0_CLIENT_SECRET,
        'audience': cfg.AUTH0_MANAGEMENT_API_AUDIENCE,
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


async def get_resource_server_scopes() -> list[dict[str, Any]]:
    """Retrieves all defined scopes for the Auth0 API (Resource Server).

    Returns:
        list[dict[str, Any]]: A list of scope dictionaries containing 'value' and 'description'.
    """
    token = await get_management_api_token()
    headers = {'Authorization': f'Bearer {token}'}
    async with httpx.AsyncClient(headers=headers) as client:
        response_json = await _handle_auth0_request(
            client, 'GET', cfg.RESOURCE_SERVER_URL, 'getting resource server scopes'
        )
        return response_json.get('scopes', [])


def get_management_api_authorized_client(token: str) -> httpx.AsyncClient:
    """Returns an httpx.AsyncClient configured with the management API token.

    Args:
        token: The Auth0 Management API access token.

    Returns:
        httpx.AsyncClient: An authenticated client instance.
    """
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
    client = httpx.AsyncClient(headers=headers)
    return client


async def create_permission_scope(permission_name: str, permission_description: str) -> list[dict[str, Any]]:
    """Creates a new permission scope for the Auth0 API.

    Args:
        permission_name: The value/name of the permission scope (e.g., 'read:reports').
        permission_description: A human-readable description of the permission.

    Returns:
        list[dict[str, Any]]: The updated list of all scopes for the Resource Server.
    """
    token = await get_management_api_token()
    # Note: Optimization - we could cache scopes perhaps, but for creation we want fresh state.
    current_scopes = await get_resource_server_scopes()
    client = get_management_api_authorized_client(token)

    new_scope_obj = {
        'value': permission_name,
        'description': permission_description,
    }

    if any(scope['value'] == permission_name for scope in current_scopes):
        print(f'Permission scope "{permission_name}" already exists. Skipping creation.')
        return current_scopes

    updated_scopes = current_scopes + [new_scope_obj]
    payload = {'scopes': updated_scopes}

    async with client:
        response_json = await _handle_auth0_request(
            client, 'PATCH', cfg.RESOURCE_SERVER_URL, 'creating permission scope', json=payload
        )
        return response_json.get('scopes', [])


async def delete_permission_scope(permission_name: str) -> list[dict[str, Any]]:
    """Deletes a permission scope from the Auth0 API.

    Args:
        permission_name: The name of the permission scope to delete.

    Returns:
        list[dict[str, Any]]: The updated list of all scopes for the Resource Server.
    """
    token = await get_management_api_token()
    current_scopes = await get_resource_server_scopes()
    client = get_management_api_authorized_client(token)

    updated_scopes = [scope for scope in current_scopes if scope['value'] != permission_name]
    payload = {'scopes': updated_scopes}

    async with client:
        response_json = await _handle_auth0_request(
            client, 'PATCH', cfg.RESOURCE_SERVER_URL, 'deleting permission scope', json=payload
        )
        return response_json.get('scopes', [])


async def assign_permission_to_user(user_id: str, permission_name: str) -> dict[str, str]:
    """Assigns a permission to a specific Auth0 user.

    Args:
        user_id: The Auth0 user ID (e.g., 'auth0|12345').
        permission_name: The name of the permission to assign.

    Returns:
        dict[str, str]: A success message dictionary.

    Raises:
        HTTPException: For Unauthorized, Not Found, or other API errors.
    """
    token = await get_management_api_token()
    url = f'https://{cfg.AUTH0_DOMAIN}/api/v2/users/{user_id}/permissions'
    headers = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}
    payload = {
        'permissions': [
            {
                'permission_name': permission_name,
                'resource_server_identifier': cfg.AUTH0_API_AUDIENCE,
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return {'message': f'Permission "{permission_name}" assigned to user "{user_id}"'}
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
            elif e.response.status_code == status.HTTP_409_CONFLICT:
                return {'message': f"Permission '{permission_name}' already assigned to user '{user_id}'"}
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


async def get_user_profile_by_id(user_id: str) -> dict[str, str | None] | None:
    """Fetches a user's public profile (name, picture, nickname) from the Auth0 Management API.

    Args:
        user_id: The Auth0 user ID.

    Returns:
        dict[str, str | None] | None: A dictionary with 'name', 'picture', 'nickname' or None if not found.
    """
    token = await get_management_api_token()
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://{cfg.AUTH0_DOMAIN}/api/v2/users/{user_id}'

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
            if e.response.status_code == status.HTTP_404_NOT_FOUND:
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


async def search_users(search_query: str | None = None, page: int = 0, per_page: int = 50) -> list[dict[str, Any]]:
    """Searches for users in Auth0, with pagination.

    Args:
        search_query: Lucene query string (e.g. 'email:"foo@bar.com"').
        page: Page index (0-based).
        per_page: Number of items per page.

    Returns:
        list[dict[str, Any]]: A list of user profile dictionaries containing only essential fields.
    """
    token = await get_management_api_token()
    headers = {'Authorization': f'Bearer {token}'}

    fields_to_include = 'user_id,name,email,picture,nickname'

    params = {
        'per_page': str(per_page),
        'page': str(page),
        'include_fields': 'true',
        'fields': fields_to_include,
        'search_engine': 'v3',
    }

    if search_query:
        params['q'] = search_query

    url = f'https://{cfg.AUTH0_DOMAIN}/api/v2/users'

    async with httpx.AsyncClient(headers=headers) as client:
        response_json = await _handle_auth0_request(client, 'GET', url, 'searching users', params=params)
        return response_json if isinstance(response_json, list) else []
