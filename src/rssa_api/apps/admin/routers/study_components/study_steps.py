"""Router for managing study steps in the admin API."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import OrderedListItem, ReorderPayloadSchema
from rssa_api.data.schemas.study_components import StudyStepPageCreate, StudyStepPageRead, StudyStepRead
from rssa_api.data.services.dependencies import StudyStepPageServiceDep, StudyStepServiceDep, StudyServiceDep
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.auth.security import get_current_user

from ...docs import ADMIN_STUDY_STEPS_TAG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix='/steps',
    tags=[ADMIN_STUDY_STEPS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user), Depends(get_auth0_authenticated_user)],
)


@router.get('/{step_id}', response_model=StudyStepRead)
async def get_study_step(
    step_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
):
    """Get details of a specific study step.

    Args:
        step_id: The UUID of the step.
        step_service: The study step service.
        _: Auth check.

    Raises:
        HTTPException: If step is not found.

    Returns:
        The study step details.
    """
    return study_step

    # Check authorization
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_step.study_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    return study_step


@router.get('/{step_id}/pages', response_model=list[OrderedListItem])
async def get_pages_for_study_step(
    step_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('read:pages', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
):
    """Get pages associated with a study step.

    Args:
        step_id: The UUID of the step.
        page_service: The page service.
        page_service: The page service.
        _: Auth check.

    Returns:
        A list of ordered pages for the step.
    """
    return [OrderedListItem.model_validate(p) for p in pages_from_db]

    # Validate access to parent step/study
    step = await step_service.get(step_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(step.study_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    pages_from_db = await page_service.get_items_for_owner_as_ordered_list(step_id)

    return [OrderedListItem.model_validate(p) for p in pages_from_db]


@router.post('/{step_id}/pages', status_code=status.HTTP_201_CREATED, response_model=StudyStepPageRead)
async def create_page_for_step(
    step_id: uuid.UUID,
    new_page: StudyStepPageCreate,
    step_service: StudyStepServiceDep,
    page_service: StudyStepPageServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:pages', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
):
    """Create a new page for a study step.

    Args:
        step_id: The UUID of the step.
        new_page: Data for the new page.
        step_service: The study step service (to verify step exists).
        page_service: The page service.
        _: Auth check.

    Raises:
        HTTPException: If the step is not found.

    Returns:
        The created page details.
    """
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    # Check authorization
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(step.study_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    created_page = await page_service.create_for_owner(step_id, new_page, study_id=step.study_id)
    page_dict = {
        'id': created_page.id,
        'created_at': created_page.created_at,
        'updated_at': created_page.updated_at,
        'enabled': created_page.enabled,
        'page_type': created_page.page_type,
        'name': created_page.name,
        'description': created_page.description,
        'title': created_page.title,
        'instructions': created_page.instructions,
        'study_id': created_page.study_id,
        'study_step_id': created_page.study_step_id,
        'order_position': created_page.order_position,
        'study_step_page_contents': [],
    }

    return StudyStepPageRead.model_validate(page_dict)


@router.patch('/{step_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_study_step(
    step_id: uuid.UUID,
    payload: dict[str, str],
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:steps', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
):
    """Update a study step.

    Args:
        step_id: The UUID of the step to update.
        payload: Fields to update.
        step_service: The study step service.
        _: Auth check.

    Returns:
        Status message.
    """
    step = await step_service.get(step_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    # Check authorization
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(step.study_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    await step_service.update(step_id, payload)

    return {'Status': 'Success'}


@router.delete('/{step_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_step(
    step_id: uuid.UUID,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:steps', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
):
    """Delete a study step.

    Args:
        step_id: The UUID of the step to delete.
        step_service: The study step service.
        _: Auth check.

    Returns:
        Empty dictionary on success.
    """
    step = await step_service.get(step_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    # Check authorization
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(step.study_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    await step_service.delete(step_id)

    return {}


@router.patch('/{step_id}/pages/reorder', status_code=status.HTTP_204_NO_CONTENT)
async def reorder_step_pages(
    step_id: uuid.UUID,
    payload: list[ReorderPayloadSchema],
    page_service: StudyStepPageServiceDep,
    study_service: StudyServiceDep,
    step_service: StudyStepServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:pages', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
):
    """Reorder pages within a study step.

    Args:
        step_id: The UUID of the step.
        payload: List of page IDs and new positions.
        page_service: The page service.
        user: Auth check.

    Returns:
        Empty dictionary on success.
    """
    step = await step_service.get(step_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    # Check authorization
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(step.study_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    pages_map = {item.id: item.order_position for item in payload}
    await page_service.reorder_items(step_id, pages_map)

    return {}
