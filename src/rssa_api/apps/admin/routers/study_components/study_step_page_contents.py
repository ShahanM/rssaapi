"""Router for managing study step page content in the admin API."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema, UserSchema
from rssa_api.data.schemas.study_components import StudyStepPageContentUpdate
from rssa_api.data.services.dependencies import (
    StudyServiceDep,
    StudyStepPageContentServiceDep,
    StudyStepPageServiceDep,
    StudyStepServiceDep,
)

from ...docs import ADMIN_SURVEY_PAGES_TAG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
    prefix='/contents',
    tags=[ADMIN_SURVEY_PAGES_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.delete('/{content_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_survey_construct_from_page(
    content_id: uuid.UUID,
    service: StudyStepPageContentServiceDep,
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:content', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Remove a survey construct from a page.

    Args:
        content_id: The UUID of the content to remove.
        service: The page content service.
        page_service: The page service.
        step_service: The step service.
        study_service: The study service.
        user: Auth check.
        current_user: The current user.

    Returns:
        Empty dictionary on success.
    """
    content = await service.get(content_id)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        page = await page_service.get(content.study_step_page_id)
        if not page:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')

        step = await step_service.get(page.step_id)
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')

        has_access = await study_service.check_study_access(step.study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')

    await service.delete(content_id)

    return {}


@router.patch('/{content_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_page_content(
    content_id: uuid.UUID,
    payload: StudyStepPageContentUpdate,
    service: StudyStepPageContentServiceDep,
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:content', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Update page content (e.g., preamble).

    Args:
        content_id: The UUID of the content.
        payload: Fields to update.
        service: The page content service.
        page_service: The page service.
        step_service: The step service.
        study_service: The study service.
        user: Auth check.
        current_user: The current user.

    Returns:
        Status message.
    """
    content = await service.get(content_id)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        page = await page_service.get(content.study_step_page_id)
        if not page:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')

        step = await step_service.get(page.step_id)
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')

        has_access = await study_service.check_study_access(step.study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Content not found.')

    await service.update(content_id, payload.model_dump(exclude_unset=True))
