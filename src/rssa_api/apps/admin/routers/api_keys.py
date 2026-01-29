"""Router for managing API keys."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.data.schemas.study_components import ApiKeyRead
from rssa_api.data.services.dependencies import ApiKeyServiceDep

router = APIRouter(
    prefix='/api-keys',
    tags=['API Keys'],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get(
    '/',
    response_model=list[ApiKeyRead],
    summary='Get API keys.',
    description="""
    Retrieve all API keys for a given study and the current user.
    """,
)
async def get_api_keys(
    service: ApiKeyServiceDep,
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    study_id: uuid.UUID = Query(),
) -> list[ApiKeyRead]:
    """Get API keys.

    Args:
        service: The API key service.
        current_user: The authenticated user.
        study_id: The study ID.

    Returns:
        List of API keys.
    """
    keys = await service.get_api_keys_for_study(study_id, current_user.id)

    return keys
