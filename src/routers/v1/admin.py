from datetime import datetime, timedelta
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from compute.utils import *

# generated with openssl rand -hex 32
SECRET_KEY = 'aea198f49eaa87c3b3082fe9dbbdca9e50c336c3ec79c3e7616ee4e305606e45'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 300

fake_users_db = {
	'johndoe': {
		'username': 'johndoe',
		'full_name': 'John Doe',
		'email': 'johndoe@example.com',
		'hashed_password': '$2b$12$DfV.lMTPVnkEf5oJST2FC.oQJop4BAUrh1dlyiTL1sEAk1Wxz/scG',
		'disabled': False,
	},
	'alice': {
		'username': 'alice',
		'full_name': 'Alice Wonderson',
		'email': 'alice@example.com',
		'hashed_password': 'fakehashedsecret2',
		'disabled': True,
	},
}


router = APIRouter()

# Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# Dependency

class Token(BaseModel):
	access_token: str
	token_type: str


class TokenData(BaseModel):
	username: Union[str, None] = None


class AdminUser(BaseModel):
	username: str
	email: Union[str, None] = None
	full_name: Union[str, None] = None
	disabled: Union[bool, None] = None


class UserInDB(AdminUser):
	hashed_password: str


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def verify_password(plain_password, hashed_password):
	# print(pwd_context.hash(plain_password), hashed_password)
	return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
	return pwd_context.hash(password)


def get_user(db, username: str):
	if username in db:
		user_dict = db[username]
		return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
	user = get_user(fake_db, username)
	if not user:
		return False
	if not verify_password(password, user.hashed_password):
		print(user)
		return False
	return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
	to_encode = data.copy()
	if expires_delta:
		expire = datetime.utcnow() + expires_delta
	else:
		expire = datetime.utcnow() + timedelta(minutes=15)
	to_encode.update({'exp': expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail='Could not validate credentials',
		headers={'WWW-Authenticate': 'Bearer'},
	)
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username: Union[str, None] = payload.get('sub')
		if username is None:
			raise credentials_exception
		token_data = TokenData(username=username)
	except JWTError:
		raise credentials_exception

	assert token_data.username is not None
	user = get_user(fake_users_db, username=token_data.username)
	if user is None:
		raise credentials_exception
	return user


async def get_current_active_user(current_user: AdminUser = Depends(get_current_user)):
	if current_user.disabled:
		raise HTTPException(status_code=400, detail='Inactive user')
	return current_user


@router.post('/token', tags=['admin'])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
	user = authenticate_user(fake_users_db, form_data.username, form_data.password)
	if not user:
		raise HTTPException(
			status_code=400,
			detail='Incorrect username or password',
			headers={'WWW-Authenticate': 'Bearer'}
		)
		print("tello")
	access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	access_token = create_access_token(
		data={'sub': user.username}, expires_delta=access_token_expires
	)
	print("token", access_token)
	return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/users/me', response_model=AdminUser, tags=['admin'])
async def read_users_me(current_user: AdminUser=Depends(get_current_active_user)):
	return current_user
