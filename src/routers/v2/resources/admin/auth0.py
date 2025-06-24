import json
from typing import Annotated, List, Optional, Union

import httpx
from async_lru import alru_cache
from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from jose.exceptions import JWTClaimsError, JWTError
from pydantic import BaseModel

import config as cfg

# from data.models.schemas.studyschema import Auth0UserSchema

AUTH0_DOMAIN = cfg.get_env_var('AUTH0_DOMAIN', '')
AUTH0_MANAGEMENT_API_AUDIENCE = cfg.get_env_var('AUTH0_MANAGEMENT_API_AUDIENCE', '')
AUTH0_API_AUDIENCE = cfg.get_env_var('AUTH0_API_AUDIENCE', '')
AUTH0_ALGORITHMS = cfg.get_env_var('AUTH0_ALGORITHMS', None)
AUTH0_MANAGEMENT_API_ID = cfg.get_env_var('AUTH0_MANAGEMENT_API_ID', '')
AUTH0_CLIENT_ID = cfg.get_env_var('AUTH0_CLIENT_ID', '')
AUTH0_CLIENT_SECRET = cfg.get_env_var('AUTH0_CLIENT_SECRET', '')
AUTH0_API_ID = cfg.get_env_var('AUTH0_API_ID', '')

# Derived URLs
AUTH0_JWKS_URL = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
AUTH0_ISSUER_URL = f'https://{AUTH0_DOMAIN}/'
RESOURCE_SERVER_URL = f'https://{AUTH0_DOMAIN}/api/v2/resource-servers/{AUTH0_API_ID}'

if AUTH0_ALGORITHMS is None:
	AUTH0_ALGORITHMS = ['']

REQUIRED_AUTH0_VARS = [
	AUTH0_DOMAIN,
	AUTH0_API_AUDIENCE,
	AUTH0_ALGORITHMS[0],
	AUTH0_MANAGEMENT_API_ID,
	AUTH0_CLIENT_ID,
	AUTH0_CLIENT_SECRET,
	AUTH0_API_ID,
]
if any(var == '' for var in REQUIRED_AUTH0_VARS):
	# In a real app, use a proper logger here
	print(
		'CRITICAL ERROR: One or more required Auth0 environment variables are not set. \
			Auth0-protected routes may not function correctly.'
	)
	# You might set a global flag or raise an exception here if you want to prevent startup
	# raise ValueError("Missing Auth0 environment variables.")
	routes_disabled = True  # Example flag for conditional route inclusion
else:
	routes_disabled = False

# routes_disabled = False
# if any([AUTH0_DOMAIN == '', AUTH0_API_AUDIENCE == '', AUTH0_ALGORITHMS[0] == '', AUTH0_CLIENT_ID == '']):
# 	routes_disabled = True
# 	raise Warning('One or more required Auth0 environment variables are not set.\n Admin routes disabled.')


router = APIRouter()


class Auth0UserSchema(BaseModel):
	"""
	Represents an authenticated user from Auth0 JWT.
	Claims are parsed from the access token payload.

	Args:
		BaseModel (_type_): _description_
	"""

	# iss: str
	sub: str
	# aud: List[str]
	# iat: int
	# exp: int
	# scope: str
	# azp: str
	permissions: List[str]
	email: Optional[str]
	name: Optional[str]
	picture: Optional[str]


# async def get_management_api_token() -> str:
# 	url = f'https://{AUTH0_DOMAIN}/oauth/token'
# 	headers = {'Content-Type': 'application/json'}
# 	payload = {
# 		'client_id': AUTH0_CLIENT_ID,
# 		'client_secret': AUTH0_CLIENT_SECRET,
# 		'audience': AUTH0_MANAGEMENT_API_AUDIENCE,
# 		'grant_type': 'client_credentials',
# 	}

# 	token = ''

# 	async with httpx.AsyncClient() as client:
# 		try:
# 			response = await client.post(url, headers=headers, json=payload)
# 			response.raise_for_status()
# 			token = response.json().get('access_token')
# 			if not token:
# 				raise HTTPException(
# 					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to obtain management API token'
# 				)
# 		except httpx.ConnectTimeout as e:
# 			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
# 		except httpx.HTTPError as e:
# 			print(f'HTTP Error: {e}')
# 			print(f'Response status: {response.status_code}')
# 			try:
# 				error_data = response.json()
# 				print(f'Response JSON: {error_data}')
# 			except json.JSONDecodeError:
# 				print(f'Response Text: {response.text}')

# 	return token


# --- Auth0 Management API Token Caching and Retrieval ---
# Cache management token for 5 minutes (300 seconds)
# Auth0 management tokens typically last for 24 hours, so a 5-minute cache is safe.
@alru_cache(maxsize=128, ttl=3600)
async def get_management_api_token_cached() -> str:
	"""Fetches and caches the Auth0 Management API token.

	Returns:
		str: _description_
	"""
	url = f'https://{AUTH0_DOMAIN}/oauth/token'
	headers = {'Content-Type': 'application/json'}
	payload = {
		'client_id': AUTH0_MANAGEMENT_API_ID,  # Use Management API Client ID
		'client_secret': AUTH0_CLIENT_SECRET,
		'audience': AUTH0_MANAGEMENT_API_AUDIENCE,
		'grant_type': 'client_credentials',
	}
	async with httpx.AsyncClient() as client:
		try:
			response = await client.post(url, headers=headers, json=payload)
			response.raise_for_status()
			token = response.json().get('access_token')
			if not token:
				raise HTTPException(
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
					detail='Auth0: Failed to obtain management API token (no access_token in response).',
				)
			return token
		except httpx.ConnectTimeout as e:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
				detail=f'Auth0: Connection timeout while obtaining management API token: {e}',
			) from e
		except httpx.HTTPStatusError as e:
			detail_msg = (
				f'Auth0: HTTP error obtaining management API token: {e.response.status_code} - {e.response.text}'
			)
			raise HTTPException(status_code=e.response.status_code, detail=detail_msg) from e
		except json.JSONDecodeError as e:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail='Auth0: Failed to decode JSON response when getting management API token.',
			) from e
		except Exception as e:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail=f'Auth0: Unexpected error obtaining management API token: {e}',
			) from e


# --- HTTP Client for Management API ---
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


# --- Auth0 Management API Operations (for permissions management) ---
async def get_resource_server_scopes() -> List[dict]:
	"""Retrieves all defined scopes for the Auth0 API (Resource Server).

	Raises:
		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_

	Returns:
		List[dict]: _description_
	"""
	token = await get_management_api_token_cached()
	client = get_management_api_authorized_client(token)

	async with client:
		try:
			response = await client.get(RESOURCE_SERVER_URL)
			response.raise_for_status()
			response_json = response.json()
			if not response_json:
				raise HTTPException(
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
					detail='Auth0: Failed to obtain resource server data (empty response).',
				)
			if 'scopes' not in response_json:
				raise HTTPException(
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
					detail='Auth0: Failed to obtain resource server scopes (missing "scopes" field).',
				)
			return response_json.get('scopes', [])
		except httpx.HTTPStatusError as e:
			raise HTTPException(
				status_code=e.response.status_code,
				detail=f'Auth0: HTTP error getting resource server scopes: {e.response.text}',
			) from e
		except json.JSONDecodeError as e:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail='Auth0: Failed to decode JSON response for resource server scopes.',
			) from e
		except Exception as e:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail=f'Auth0: Unexpected error getting resource server scopes: {e}',
			) from e


async def create_permission_scope(permission_name: str, permission_description: str) -> List[dict]:
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
	token = await get_management_api_token_cached()
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


async def delete_permission_scope(permission_name: str) -> List[dict]:
	"""Deletes a permission scope from the AUth0 API

	Args:
		permission_name (str): _description_

	Raises:
		HTTPException: _description_
		HTTPException: _description_

	Returns:
		List[dict]: _description_
	"""
	token = await get_management_api_token_cached()
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
	token = get_management_api_token_cached()
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


# --- Auth0 JWT Authentication Dependency ---

# HTTPBearer will automatically parse "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer(auto_error=False)


@alru_cache  # Cache JWKS for some to avoid repeaded network calls
async def get_jwks_cached():
	"""Fetches and caches Auth0 JWKS

	Raises:
		HTTPException: _description_

	Returns:
		_type_: _description_
	"""
	async with httpx.AsyncClient() as client:
		try:
			response = await client.get(AUTH0_JWKS_URL, timeout=5)
			response.raise_for_status()
			return response.json()
		except httpx.RequestError as e:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Auth0: Could not getchc jWKS: {e}'
			) from e


async def get_auth0_authenticated_user(
	credentials: Annotated[Union[HTTPAuthorizationCredentials, None], Security(bearer_scheme)],
) -> Auth0UserSchema:
	"""FastAPI dependency to authenticate a user via Auth0 JWT
	Extracts user info and permissions from the access token.

	Args:
		credentials (Annotated[HTTPAuthorizationCredentials  |  None, Security): _description_

	Returns:
		Auth0UserSchema: _description_
	"""
	if credentials is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Bearer token missing or invalid')
	token = credentials.credentials
	jwks = await get_jwks_cached()

	try:
		unverified_header = jwt.get_unverified_header(token)
		rsa_key = {}
		for key in jwks['keys']:
			if key['kid'] == unverified_header.get('kid'):
				rsa_key = {'kty': key['kty'], 'kid': key['kid'], 'use': key['use'], 'n': key['n'], 'e': key['e']}
				break
		if not rsa_key:
			raise JWTError('Auth0: Unable to find appropriate signing key for token')

		# Decode and validate the token claims
		payload = jwt.decode(
			token,
			rsa_key,
			algorithms=AUTH0_ALGORITHMS,
			audience=AUTH0_API_AUDIENCE,
			issuer=AUTH0_ISSUER_URL,
		)

		# Basic claim validation (auth0 usually puts permissions in 'permissions' claim)
		user_id = payload.get('sub')
		permission = payload.get('permissions', [])
		email = payload.get('email')
		name = payload.get('name')
		picture = payload.get('picture')

		if not user_id:
			raise JWTClaimsError('Auth0: Token is missing "sub" claim.')

		return Auth0UserSchema(sub=user_id, permissions=permission, email=email, name=name, picture=picture)
	except JWTClaimsError as e:
		print('RAISING CAINE')
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,  # Forbidden if claims are invalid (e.g., wrong audience/issuer)
			detail=f'Auth0: Invalid token claims: {e}',
			headers={'WWW-Authenticate': 'Bearer error="invalid_token_claims"'},
		) from e
	except JWTError as e:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=f'Auth0: Invalid token: {e}',
			headers={'WWW-Authenticate': 'Bearer error="invalid_token"'},
		) from e
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f'Auth0: Authentication processing error: {e}',
			headers={'WWW-Authenticate': 'Bearer'},
		) from e


# --- Permissions Checker Dependencies (Authorization) ---


def require_permissions(permission_scope: str):
	"""FastAPI dependency factor to check if the authenticated user has a specific permission scope.

	Usage: Depends(require_permission("read:studies))

	Args:
		permission_scope (str): _description_
	"""

	def check_permission_inner(user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)]):
		if permission_scope not in user.permissions:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN, detail=f'User does not "{permission_scope}" permission.'
			)
		return user

	return check_permission_inner


# def auth0_bearer_token(request: Request):
# 	authorization = request.headers.get('Authorization')
# 	scheme, param = get_authorization_scheme_param(authorization)
# 	if not authorization or scheme.lower() != 'bearer':
# 		raise HTTPException(
# 			status_code=status.HTTP_401_UNAUTHORIZED,
# 			detail='Invalid Authorization header',
# 			headers={'WWW-Authenticate': 'Bearer'},
# 		)
# 	return param


# async def decode_jwt(token: str):
# 	jwks = await get_jwks()
# 	unverified_header = jwt.get_unverified_header(token)
# 	rsa_key = {}
# 	for key in jwks['keys']:
# 		if key['kid'] == unverified_header['kid']:
# 			rsa_key = {'kty': key['kty'], 'kid': key['kid'], 'use': key['use'], 'n': key['n'], 'e': key['e']}
# 			break
# 	try:
# 		payload = jwt.decode(
# 			token,
# 			rsa_key,
# 			algorithms=AUTH0_ALGORITHMS[0],
# 			audience=AUTH0_API_AUDIENCE,
# 			issuer=f'https://{AUTH0_DOMAIN}/',
# 			access_token=token,
# 		)
# 		return payload
# 	except JWTError as e:
# 		raise HTTPException(
# 			status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={'WWW-Authenticate': 'Bearer'}
# 		) from e


# async def get_current_user_profile(request: Request):
# 	current_user = await decode_jwt(auth0_bearer_token(request))
# 	user_profile = f'https://{auth0_domain}/userinfo'
# 	async with httpx.AsyncClient() as client:
# 		response = await client.get(user_profile, headers={'Authorization': f'Bearer {auth0_bearer_token(request)}'})
# 		response.raise_for_status()
# 		user = response.json()
# 		if current_user['sub'] != user['sub']:
# 			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Token is invalid')
# 	return user


# async def get_current_user(request: Request) -> Auth0UserSchema:
# 	token = get_management_api_token()
# 	current_user = await decode_jwt(auth0_bearer_token(request))
# 	# TODO: Check if user has read:all permission
# 	auth0user = Auth0UserSchema(**current_user)
# 	return auth0user


# async def get_current_admin_user(
# 	request: Request, required_permissions: List[str] = ['read:all', 'write:all', 'delete:all']
# ):
# 	current_user = await decode_jwt(auth0_bearer_token(request))

# 	# admin_permissions = ['read:all', 'write:all', 'delete:all']
# 	print(current_user)
# 	# admin_privileges = lambda perms: [x in perms for x in admin_permissions]
# 	if not all(perm in current_user['permissions'] for perm in required_permissions):
# 		raise HTTPException(
# 			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permission to access this route.'
# 		)
# 	return Auth0UserSchema(**current_user)
