import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user
from rssa_api.data.models.study_components import User
from rssa_api.data.schemas.study_components import ApiKeySchema
from rssa_api.data.services import ApiKeyService
from rssa_api.data.services.rssa_dependencies import get_api_key_service

router = APIRouter(
    prefix='/api-keys',
    tags=['API Keys'],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get(
    '/{key_id}',
    response_model=list[ApiKeySchema],
    summary='',
    description='',
    response_description='',
)
async def get_api_keys(
    key_id: uuid.UUID,
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    study_id: uuid.UUID = Query(),
):
    keys = await service.get_api_keys_for_study(study_id, current_user.id)

    return keys
