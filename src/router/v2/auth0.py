import json
from typing import List

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt

import config as cfg
from data.models.schemas.studyschema import Auth0UserSchema

AUTH0_DOMAIN = cfg.get_env_var('AUTH0_DOMAIN', '')
AUTH0_MANAGEMENT_API_AUDIENCE = cfg.get_env_var('AUTH0_MANAGEMENT_API_AUDIENCE', '')
AUTH0_API_AUDIENCE = cfg.get_env_var('AUTH0_API_AUDIENCE', '')
AUTH0_ALGORITHMS = [cfg.get_env_var('AUTH0_ALGORITHMS', '')]
AUTH0_MANAGEMENT_API_ID = cfg.get_env_var('AUTH0_MANAGEMENT_API_ID', '')
AUTH0_CLIENT_ID = cfg.get_env_var('AUTH0_CLIENT_ID', '')
AUTH0_CLIENT_SECRET = cfg.get_env_var('AUTH0_CLIENT_SECRET', '')
AUTH0_API_ID = cfg.get_env_var('AUTH0_API_ID', '')

RESOURCE_SERVER_URL = f'https://{AUTH0_DOMAIN}/api/v2/resource-servers/{AUTH0_API_ID}'

routes_disabled = False
if any([AUTH0_DOMAIN == '', AUTH0_API_AUDIENCE == '', AUTH0_ALGORITHMS[0] == '', AUTH0_CLIENT_ID == '']):
	routes_disabled = True
	raise Warning('One or more required Auth0 environment variables are not set.\n Admin routes disabled.')


router = APIRouter()


async def get_management_api_token() -> str:
	url = f'https://{AUTH0_DOMAIN}/oauth/token'
	headers = {'Content-Type': 'application/json'}
	payload = {
		'client_id': AUTH0_CLIENT_ID,
		'client_secret': AUTH0_CLIENT_SECRET,
		'audience': AUTH0_MANAGEMENT_API_AUDIENCE,
		'grant_type': 'client_credentials',
	}

	token = ''

	async with httpx.AsyncClient() as client:
		try:
			response = await client.post(url, headers=headers, json=payload)
			response.raise_for_status()
			token = response.json().get('access_token')
			if not token:
				raise HTTPException(
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to obtain management API token'
				)
		except httpx.ConnectTimeout as e:
			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
		except httpx.HTTPError as e:
			print(f'HTTP Error: {e}')
			print(f'Response status: {response.status_code}')
			try:
				error_data = response.json()
				print(f'Response JSON: {error_data}')
			except json.JSONDecodeError:
				print(f'Response Text: {response.text}')

	return token


def get_management_api_authorized_client(token: str) -> httpx.AsyncClient:
	headers = {'authorization': f'Bearer {token}', 'content-type': 'application/json', 'cache-control': 'no-cache'}

	client = httpx.AsyncClient()
	client.headers.update(headers)

	return client


async def get_resource_server_scopes(token: str) -> List[dict]:
	client = get_management_api_authorized_client(token)

	scopes = []

	async with client:
		try:
			response = await client.get(RESOURCE_SERVER_URL)
			response.raise_for_status()
			response_json = response.json()
			if not response_json:
				raise HTTPException(
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to obtain resource server data'
				)
			if 'scopes' not in response_json:
				raise HTTPException(
					status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to obtain resource server scopes'
				)
			scopes = response_json.get('scopes', [])

		except httpx.HTTPError as e:
			print(f'HTTP Error: {e}')
			print(f'Response status: {response.status_code}')
			try:
				error_data = response.json()
				print(f'Response JSON: {error_data}')
			except json.JSONDecodeError:
				print(f'Response Text: {response.text}')

	return scopes


async def create_permission_scope(permission_name, permission_description) -> List[dict]:
	token = await get_management_api_token()
	scopes = await get_resource_server_scopes(token)

	client = get_management_api_authorized_client(token)

	new_scope_response = []

	new_scope = {
		'value': permission_name,
		'description': permission_description,
	}

	scopes.append(new_scope)
	payload = {'scopes': scopes}
	async with client:
		try:
			response = await client.patch(RESOURCE_SERVER_URL, json=payload)
			response.raise_for_status()
			response_json = response.json()
			new_scope_response = response_json.get('scopes', [])
		except httpx.ConnectTimeout as e:
			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
		except httpx.HTTPError as e:
			print(f'HTTP Error: {e}')
			print(f'Response status: {response.status_code}')
			try:
				error_data = response.json()
				print(f'Response JSON: {error_data}')
			except json.JSONDecodeError:
				print(f'Response Text: {response.text}')

	return new_scope_response


async def delete_permission_scope(permission_name) -> List[dict]:
	token = await get_management_api_token()
	scopes = await get_resource_server_scopes(token)

	client = get_management_api_authorized_client(token)
	new_scope_response = []

	scopes = [scope for scope in scopes if scope['value'] != permission_name]
	payload = {'scopes': scopes}
	async with client:
		try:
			response = await client.patch(RESOURCE_SERVER_URL, json=payload)
			response.raise_for_status()
			response_json = response.json()
			new_scope_response = response_json.get('scopes', [])
		except httpx.ConnectTimeout as e:
			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
		except httpx.HTTPError as e:
			print(f'HTTP Error: {e}')
			print(f'Response status: {response.status_code}')
			try:
				error_data = response.json()
				print(f'Response JSON: {error_data}')
			except json.JSONDecodeError:
				print(f'Response Text: {response.text}')
				raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
	return new_scope_response


async def assign_permission_to_user(user_id, permission_name):
	token = get_management_api_token()
	url = f'{AUTH0_API_AUDIENCE}users/{user_id}/permissions'
	headers = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
	payload = {'permissions': [{'permission_name': permission_name, 'resource_server_identifier': auth0_domain}]}
	async with httpx.AsyncClient() as client:
		try:
			response = await client.post(url, headers=headers, json=payload)
			response.raise_for_status()

			return response.json()
		except httpx.ConnectTimeout as e:
			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
		except httpx.HTTPStatusError as e:
			if e.response.status_code == 401:
				raise HTTPException(
					status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid client credentials'
				) from e
			elif e.response.status_code == 404:
				raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found') from e
			else:
				raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


def auth0_bearer_token(request: Request):
	authorization = request.headers.get('Authorization')
	scheme, param = get_authorization_scheme_param(authorization)
	if not authorization or scheme.lower() != 'bearer':
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Invalid Authorization header',
			headers={'WWW-Authenticate': 'Bearer'},
		)
	return param


async def get_jwks():
	url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
	async with httpx.AsyncClient() as client:
		try:
			response = await client.get(url)
			response.raise_for_status()
			return response.json()
		except httpx.ConnectTimeout as e:
			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e


async def decode_jwt(token: str):
	jwks = await get_jwks()
	unverified_header = jwt.get_unverified_header(token)
	rsa_key = {}
	for key in jwks['keys']:
		if key['kid'] == unverified_header['kid']:
			rsa_key = {'kty': key['kty'], 'kid': key['kid'], 'use': key['use'], 'n': key['n'], 'e': key['e']}
			break
	try:
		payload = jwt.decode(
			token,
			rsa_key,
			algorithms=AUTH0_ALGORITHMS[0],
			audience=AUTH0_API_AUDIENCE,
			issuer=f'https://{AUTH0_DOMAIN}/',
			access_token=token,
		)
		return payload
	except JWTError as e:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={'WWW-Authenticate': 'Bearer'}
		) from e


async def get_current_user_profile(request: Request):
	current_user = await decode_jwt(auth0_bearer_token(request))
	user_profile = f'https://{auth0_domain}/userinfo'
	async with httpx.AsyncClient() as client:
		response = await client.get(user_profile, headers={'Authorization': f'Bearer {auth0_bearer_token(request)}'})
		response.raise_for_status()
		user = response.json()
		if current_user['sub'] != user['sub']:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Token is invalid')
	return user


async def get_current_user(request: Request) -> Auth0UserSchema:
	token = get_management_api_token()
	current_user = await decode_jwt(auth0_bearer_token(request))
	# TODO: Check if user has read:all permission
	auth0user = Auth0UserSchema(**current_user)
	return auth0user


async def get_current_admin_user(
	request: Request, required_permissions: List[str] = ['read:all', 'write:all', 'delete:all']
):
	current_user = await decode_jwt(auth0_bearer_token(request))

	# admin_permissions = ['read:all', 'write:all', 'delete:all']
	print(current_user)
	# admin_privileges = lambda perms: [x in perms for x in admin_permissions]
	if not all(perm in current_user['permissions'] for perm in required_permissions):
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permission to access this route.'
		)
	return Auth0UserSchema(**current_user)
