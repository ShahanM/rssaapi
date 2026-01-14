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
    """Validates the study API key credentials.

    Args:
        api_key_id: The unique identifier for the API key.
        api_key_secret: The secret associated with the API key.
        key_service: The service dependency to lookup and validate keys.

    Returns:
        uuid.UUID: The study_id associated with the valid API key.

    Raises:
        HTTPException: If the key is invalid or inactive (401).
    """
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
    """Validates the X-Api-Key and ensures it belongs to the correct, active study.

    Args:
        study_id: The study ID from the URL path.
        valid_study_id: The study ID derived from the validated API key.

    Returns:
        uuid.UUID: The validated study ID.

    Raises:
        HTTPException: If the API key does not match the requested study (403).
    """
    if study_id != valid_study_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='API key is not authorized to make this request.'
        )

    return valid_study_id


async def get_current_participant(
    token: Annotated[str, Depends(oauth2_scheme)],
    participant_service: StudyParticipantServiceDep,
) -> StudyParticipantRead:
    """Decodes the JWT to retrieve the current study participant.

    Args:
        token: The bearer token from the request.
        participant_service: The service to retrieve participant details.

    Returns:
        StudyParticipantRead: The participant schema.

    Raises:
        HTTPException: If the token is invalid, expired, or the participant is not found (401).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        participant_id: str | None = payload.get('sub')
        if participant_id is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    participant = await participant_service.get(uuid.UUID(participant_id))

    if participant is None:
        raise credentials_exception

    return StudyParticipantRead.model_validate(participant)


async def validate_study_participant(
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipantRead, Depends(get_current_participant)],
) -> dict[str, uuid.UUID]:
    """Ensures the authenticated participant belongs to the authenticated study.

    Args:
        study_id: The study ID from the API key.
        participant: The authenticated participant.

    Returns:
        dict[str, uuid.UUID]: A dictionary containing 'sid' (Study ID) and 'pid' (Participant ID).

    Raises:
        HTTPException: If the participant is not part of the study (403).
    """
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')
    return {'sid': study_id, 'pid': participant.id}


def generate_jwt_token_for_payload(payload: dict[str, str], algorithm: str = 'HS256') -> str:
    """Generates a JWT token for the given payload using the configured secret key.

    Args:
        payload: The claims to include in the token.
        algorithm: The signing algorithm. Defaults to 'HS256'.

    Returns:
        str: The encoded JWT token.

    Raises:
        HTTPException: If token generation fails (500).
    """
    try:
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=algorithm)
        return jwt_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='There was a problem with the security key.'
        ) from e
