"""Authorization methods."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt

from rssa_api.core.config import get_env_var
from rssa_api.data.schemas.participant_schemas import StudyParticipantRead
from rssa_api.data.services.dependencies import ApiKeyServiceDep, StudyParticipantServiceDep

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
    key_service: ApiKeyServiceDep,
) -> uuid.UUID:
    """Validates the study API key credentials."""
    valid_key = await key_service.validate_api_key(api_key_id, api_key_secret)
    if not valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or inactive API Key.',
        )
    return valid_key.study_id


async def decode_jwt(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, str]:
    """Decodes the JWT and returns a dictionary of the JWT content."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        participant_id: str | None = payload.get('sub')
        session_id: str | None = payload.get('sid')
        study_id: str | None = payload.get('sty')
        expires_at: str | None = payload.get('exp')  # TODO: check expiration at some point
        if not all([participant_id, session_id, study_id]):
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    return {'sub': participant_id, 'sid': session_id, 'sty': study_id, 'exp': expires_at}


async def authorize_api_key_for_study(
    study_id: Annotated[uuid.UUID, Path()],
    valid_study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
) -> uuid.UUID:
    """Validates the X-Api-Key and ensures it belongs to the correct, active study."""
    if study_id != valid_study_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='API key is not authorized to make this request.'
        )

    return valid_study_id


async def get_current_participant(
    token_content: Annotated[dict, Depends(decode_jwt)],
    participant_service: StudyParticipantServiceDep,
) -> StudyParticipantRead:
    """Decodes the JWT to retrieve the current study participant."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    participant_id = uuid.UUID(token_content['sub'])
    participant = await participant_service.get(participant_id, StudyParticipantRead)

    if participant is None:
        raise credentials_exception

    return StudyParticipantRead.model_validate(participant)


async def validate_study_participant(
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipantRead, Depends(get_current_participant)],
) -> dict[str, uuid.UUID]:
    """Ensures the authenticated participant belongs to the authenticated study."""
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')
    return {'sty': study_id, 'sub': participant.id}


def generate_jwt_token_for_payload(payload: dict[str, str], algorithm: str = 'HS256') -> str:
    """Generates a JWT token for the given payload using the configured secret key."""
    try:
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=algorithm)
        return jwt_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='There was a problem with the security key.'
        ) from e
