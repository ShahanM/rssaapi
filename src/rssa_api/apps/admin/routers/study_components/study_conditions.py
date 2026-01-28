import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions, get_current_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.study_components import StudyConditionRead
from rssa_api.data.services.dependencies import StudyConditionServiceDep, StudyServiceDep
from rssa_api.data.schemas.auth_schemas import UserSchema

from ...docs import ADMIN_STUDY_CONDITIONS_TAG

router = APIRouter(
    prefix='/conditions',
    tags=[ADMIN_STUDY_CONDITIONS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)

from rssa_api.services.recommendation.registry import get_registry_keys


@router.get('/recommender-keys', response_model=list[dict[str, str]])
async def get_recommender_keys(
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
):
    return get_registry_keys()


@router.get('/{condition_id}', response_model=StudyConditionRead)
async def get_item(
    condition_id: uuid.UUID,
    service: StudyConditionServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
):
    condition = await service.get(condition_id)
    if condition is None:
        raise (HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.'))

    # Check authorization
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(condition.study_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.')

    return condition


@router.patch('/{condition_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_item(
    condition_id: uuid.UUID,
    service: StudyConditionServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'update:conditions'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    payload: dict[str, Any],
):
    condition = await service.get(condition_id)
    if condition is None:
        raise (HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.'))

    # Check authorization
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(condition.study_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.')

    await service.update(condition_id, payload)
    return {'status': 'success'}
