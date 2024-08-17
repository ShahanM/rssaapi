from fastapi import APIRouter, Depends, HTTPException, status, Request
from jose import jwt, JWTError
import httpx
from fastapi.security.utils import get_authorization_scheme_param
from data.models.schema.studyschema import Auth0UserSchema
import config as cfg

auth0_domain = cfg.get_env_var("AUTH0_DOMAIN")
auth0_audience = cfg.get_env_var("AUTH0_AUDIENCE")
auth0_algorithms = [cfg.get_env_var("AUTH0_ALGORITHMS")]
auth0_client_id = cfg.get_env_var("AUTH0_CLIENT_ID")


router = APIRouter()


def auth0_bearer_token(request: Request):
	authorization = request.headers.get("Authorization")
	scheme, param = get_authorization_scheme_param(authorization)
	if not authorization or scheme.lower() != 'bearer':
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Invalid Authorization header',
			headers={"WWW-Authenticate": "Bearer"}
		)
	return param


async def get_jwks():
	url = f'https://{auth0_domain}/.well-known/jwks.json'
	async with httpx.AsyncClient() as client:
		try:
			response = await client.get(url)
			response.raise_for_status()
			return response.json()
		except httpx.ConnectTimeout as e:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
				detail=str(e)
			)


async def decode_jwt(token: str):
	jwks = await get_jwks()
	unverified_header = jwt.get_unverified_header(token)
	rsa_key = {}
	for key in jwks['keys']:
		if key['kid'] == unverified_header['kid']:
			rsa_key = {
				'kty': key['kty'],
				'kid': key['kid'],
				'use': key['use'],
				'n': key['n'],
				'e': key['e']
			}
			break
	try:
		payload = jwt.decode(
			token,
			rsa_key,
			algorithms=auth0_algorithms,
			audience=auth0_audience,
			issuer=f'https://{auth0_domain}/',
			access_token=token
		)
		return payload
	except JWTError as e:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=str(e),
			headers={"WWW-Authenticate": "Bearer"}
		)
	

async def get_current_user_profile(request: Request):
	current_user = await decode_jwt(auth0_bearer_token(request))
	user_profile = f'https://{auth0_domain}/userinfo'
	async with httpx.AsyncClient() as client:
		response = await client.get(
			user_profile,
			headers={
				'Authorization': f'Bearer {auth0_bearer_token(request)}'
			}
		)
		response.raise_for_status()
		user = response.json()
		if current_user['sub'] != user['sub']:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail='Token is invalid'
			)
	return user


async def get_current_user(request: Request) -> Auth0UserSchema:
	current_user = await decode_jwt(auth0_bearer_token(request))
	# TODO: Check if user has read:all permission
	auth0user = Auth0UserSchema(**current_user)
	return auth0user


async def get_current_admin_user(request: Request):
	current_user = await decode_jwt(auth0_bearer_token(request))
	
	admin_permissions = ['read:all', 'write:all', 'delete:all']
	admin_privileges = lambda perms: [x in perms for x in admin_permissions]
	if not all(admin_privileges(current_user['permissions'])):
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail='You do not have permission to access this route.'
		)
	return current_user


@router.get('/test/')
async def test_api(current_user: dict = Depends(get_current_user)):
	""" Testing Auth0 API to authenticate user
		This is a protected route, only authenticated users can access this route
	"""
	print(current_user['permissions'])
	return {'user': current_user}


@router.get('/test2/')
async def test_api2(current_user: dict = Depends(get_current_admin_user)):
	""" Testing user roles and permissions
		This is a protected route, only authenticated users with read:all and 
		write:all permissions can access this route
	"""
	return {'user': current_user}