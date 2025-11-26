import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user
from rssa_api.data.models.study_components import User
from rssa_api.data.schemas.study_components import ApiKeySchema
from rssa_api.data.services import ApiKeyServiceDep

router = APIRouter(
    prefix='/api-keys',
    tags=['API Keys'],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get('/', response_model=list[ApiKeySchema])
async def get_api_keys(
    service: ApiKeyServiceDep,
    current_user: Annotated[User, Depends(get_current_user)],
    study_id: uuid.UUID = Query(),
):
    """Retrieve all API keys for a given study and the current user.

    Args:
        service: The ApiKeyService dependency.
        current_user: The currently authenticated user.
        study_id: The ID of the study to retrieve API keys for.

    Returns:
        A list of ApiKeySchema objects for the specified study and user.
    """
    keys = await service.get_api_keys_for_study(study_id, current_user.id)

    return keys
