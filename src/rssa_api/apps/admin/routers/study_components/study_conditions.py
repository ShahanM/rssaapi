"""Router for managing study conditions in the admin API."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.data.schemas.study_components import StudyConditionRead
from rssa_api.data.services.dependencies import StudyConditionServiceDep, StudyServiceDep
from rssa_api.services.recommendation.registry import get_registry_keys

from ...docs import ADMIN_STUDY_CONDITIONS_TAG

router = APIRouter(
    prefix='/conditions',
    tags=[ADMIN_STUDY_CONDITIONS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get('/recommender-keys', response_model=list[dict[str, str]])
async def get_recommender_keys(
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
) -> list[dict[str, str]]:
    """Get the available recommender registry keys.

    Args:
        user: The authenticated user.

    Returns:
        List of registry keys.
    """
    return get_registry_keys()


@router.get('/{condition_id}', response_model=StudyConditionRead)
async def get_item(
    condition_id: uuid.UUID,
    service: StudyConditionServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> StudyConditionRead:
    """Get a study condition by ID.

    Args:
        condition_id: The UUID of the condition.
        service: The study condition service.
        study_service: The study service.
        user: The authenticated user.
        current_user: The current user.

    Returns:
        The study condition.
    """
    condition = await service.get(condition_id)
    if condition is None:
        raise (HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.'))

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(condition.study_id, current_user.id, min_role='viewer')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.')

    return StudyConditionRead.model_validate(condition)


@router.patch('/{condition_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_item(
    condition_id: uuid.UUID,
    service: StudyConditionServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    payload: dict[str, Any],
) -> None:
    """Update a study condition.

    Args:
        condition_id: The UUID of the condition.
        service: The study condition service.
        study_service: The study service.
        user: The authenticated user.
        current_user: The current user.
        payload: The payload to update.

    Returns:
        Success status.
    """
    condition = await service.get(condition_id)
    if condition is None:
        raise (HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.'))

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(condition.study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.')

    await service.update(condition_id, payload)
