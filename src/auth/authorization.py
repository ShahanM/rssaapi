import uuid
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt

from config import get_env_var
from data.schemas.participant_schemas import ParticipantSchema
from data.services import ApiKeyService, ParticipantService
from data.services.rssa_dependencies import get_api_key_service as key_service
from data.services.rssa_dependencies import get_participant_service as participant_service

api_key_id = APIKeyHeader(
    name='X-Api-Key-Id',
    scheme_name='Api key Id',
    description='The API Key Id generated for the study making the request.',
)

api_key_secret = APIKeyHeader(
    name='X-Api-Key-Secret',
    scheme_name='Api key secret',
    description='The API Key secret generated for the study making the request.',
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

SECRET_KEY = get_env_var('RSSA_JWT_SECRET_KEY')
ALGORITHM = 'HS256'


async def validate_api_key(
    api_key_id: Annotated[uuid.UUID, Depends(api_key_id)],
    api_key_secret: Annotated[str, Depends(api_key_secret)],
    key_service: Annotated[ApiKeyService, Depends(key_service)],
) -> uuid.UUID:
    valid_key = await key_service.validate_api_key(api_key_id, api_key_secret)
    if not valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or inactive API Key.',
        )
    return valid_key.study_id


async def authorize_api_key_for_study(
    study_id: Annotated[uuid.UUID, Path()],
    valid_study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
) -> uuid.UUID:
    """
    Validates the X-Api-Key and ensures it belongs to the correct, active study.
    Returns the study ID (UUID) on success.
    """
    if study_id != valid_study_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='API key is not authorized to make this request.'
        )

    return valid_study_id


async def get_current_participant(
    token: Annotated[str, Depends(oauth2_scheme)],
    participant_service: Annotated[ParticipantService, Depends(participant_service)],
) -> ParticipantSchema:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        participant_id: Optional[str] = payload.get('sub')
        if participant_id is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    participant = await participant_service.get_participant(uuid.UUID(participant_id))

    if participant is None:
        raise credentials_exception

    return participant


async def validate_study_participant(
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[ParticipantSchema, Depends(get_current_participant)],
) -> dict[str, uuid.UUID]:
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')
    return {'sid': study_id, 'pid': participant.id}


def generate_jwt_token_for_payload(payload: dict[str, str], algorithm='HS256') -> str:
    try:
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=algorithm)
        return jwt_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='There was a problem with the security key.'
        ) from e
