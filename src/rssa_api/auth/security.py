from typing import Annotated

import httpx
from async_lru import alru_cache
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTClaimsError, JWTError
from rssa_storage.rssadb.models.study_components import User

from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import UserServiceDep

from . import config as cfg

bearer_scheme = HTTPBearer(auto_error=False)


@alru_cache
async def get_jwks_cached():
    """Fetches and caches Auth0 JWKS."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(cfg.AUTH0_JWKS_URL)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f'Auth0: Could not fetch JWKS: {e}') from e


async def validate_auth0_token(token: str) -> Auth0UserSchema:
    """Validates an Auth0 JWT and returns the user schema."""
    try:
        jwks = await get_jwks_cached()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == unverified_header.get('kid'):
                rsa_key = {'kty': key['kty'], 'kid': key['kid'], 'use': key['use'], 'n': key['n'], 'e': key['e']}
                break
        if not rsa_key:
            raise JWTError('Auth0: Unable to find appropriate signing key')

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=cfg.AUTH0_ALGORITHMS,
            audience=cfg.AUTH0_API_AUDIENCE,
            issuer=cfg.AUTH0_ISSUER_URL,
        )
        return Auth0UserSchema(**payload)
    except (JWTError, JWTClaimsError) as e:
        if isinstance(e, JWTClaimsError):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f'Auth0: Invalid token claims: {e}') from e
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f'Auth0: Invalid token: {e}') from e


async def get_auth0_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> Auth0UserSchema:
    """Dependency that validates the Auth0 token and returns the Auth0 user profile."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Bearer token missing')
    return await validate_auth0_token(credentials.credentials)


async def get_current_user(
    token_user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    user_service: UserServiceDep,
) -> User:
    """Dependency that takes the validated Auth0 user and returns the local database user."""
    db_user = await user_service.get_user_by_auth0_sub(token_user.sub)
    if db_user is None:
        db_user = await user_service.create_user_from_auth0(token_user)
    return db_user


def require_permissions(*scopes: str):
    """Dependency factory to check if the user has at least one of the required scopes."""

    def check_permission_inner(user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)]):
        if not any(scope in user.permissions for scope in scopes):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f'User lacks required permissions. Needs one of: {list(scopes)}',
            )
        return user

    return check_permission_inner
