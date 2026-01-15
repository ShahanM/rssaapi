import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from rssa_storage.rssadb.models.study_components import User

from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user
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
    current_user: Annotated[User, Depends(get_current_user)],
    study_id: uuid.UUID = Query(),
):
    keys = await service.get_api_keys_for_study(study_id, current_user.id)

    return keys
