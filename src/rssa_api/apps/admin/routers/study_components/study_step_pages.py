"""Router for managing study step pages in the admin API."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.data.schemas.base_schemas import OrderedListItem, ReorderPayloadSchema
from rssa_api.data.schemas.study_components import (
    StudyStepPageContentCreate,
    StudyStepPageContentRead,
    StudyStepPageRead,
)
from rssa_api.data.services.dependencies import (
    StudyServiceDep,
    StudyStepPageContentServiceDep,
    StudyStepPageServiceDep,
    StudyStepServiceDep,
)

from ...docs import ADMIN_STEP_PAGES_TAG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix='/pages',
    tags=[ADMIN_STEP_PAGES_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get(
    '/{page_id}',
    response_model=StudyStepPageRead,
)
async def get_step_page_details(
    page_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('read:pages', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> StudyStepPageRead:
    """Get details of a specific study step page.

    Args:
        page_id: The UUID of the page.
        page_service: The page service.
        step_service: The step service.
        study_service: The study service.
        user: Auth check.
        current_user: The current user.

    Returns:
        The study step page details.
    """
    page_from_db = await page_service.get_detailed(page_id, StudyStepPageRead)
    if not page_from_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        step = await step_service.get(page_from_db.study_step_id)
        if step:
            has_access = await study_service.check_study_access(step.study_id, current_user.id, min_role='viewer')
            if not has_access:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    return StudyStepPageRead.model_validate(page_from_db)


@router.patch(
    '/{page_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Update a study step page.',
    description="""
    Updates an existing study step page with the provided fields.
    """,
    response_description='Status of the operation.',
)
async def update_step_page(
    page_id: uuid.UUID,
    updated_page: dict[str, str],
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:pages', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Update a study step page.

    Args:
        page_id: The UUID of the page to update.
        updated_page: Dictionary of fields to update.
        page_service: The page service.
        step_service: The step service.
        study_service: The study service.
        user: Auth check.
        current_user: The current user.

    Returns:
        Status message.
    """
    page = await page_service.get(page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        step = await step_service.get(page.study_step_id)
        if step:
            has_access = await study_service.check_study_access(step.study_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    await page_service.update(page_id, updated_page)


@router.delete(
    '/{page_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete a study step page.',
    description="""
    Deletes a study step page by its ID.
    """,
    response_description='Status of the operation.',
)
async def delete_step_page(
    page_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:pages', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Delete a study step page.

    Args:
        page_id: The UUID of the page to delete.
        page_service: The page service.
        step_service: The step service.
        study_service: The study service.
        user: Auth check.
        current_user: The current user.

    Returns:
        Status message.
    """
    page = await page_service.get(page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        step = await step_service.get(page.study_step_id)
        if step:
            has_access = await study_service.check_study_access(step.study_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    await page_service.delete(page_id)


@router.get(
    '/{page_id}/contents',
    response_model=list[OrderedListItem],
)
async def get_page_content(
    page_id: uuid.UUID,
    content_service: StudyStepPageContentServiceDep,
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('read:content', 'admin:all')),
    ],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> list[OrderedListItem]:
    """Get content items associated with a page.

    Args:
        page_id: The UUID of the page.
        content_service: The page content service.
        page_service: The page service.
        step_service: The step service.
        study_service: The study service.
        user: Auth check.
        current_user: The current user.

    Returns:
        A list of ordered content items.
    """
    page = await page_service.get(page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        step = await step_service.get(page.study_step_id)
        if step:
            has_access = await study_service.check_study_access(step.study_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    content = await content_service.get_items_for_owner_as_ordered_list(page_id)

    return [OrderedListItem.model_validate(c) for c in content]


@router.post(
    '/{page_id}/contents',
    status_code=status.HTTP_201_CREATED,
    response_model=StudyStepPageContentRead,
)
async def add_content_to_page(
    page_id: uuid.UUID,
    new_content: StudyStepPageContentCreate,
    content_service: StudyStepPageContentServiceDep,
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('create:content', 'admin:all')),
    ],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> StudyStepPageContentRead:
    """Add content to a study step page.

    Args:
        page_id: The UUID of the page.
        new_content: The content to add.
        content_service: The content service.
        page_service: The page service.
        step_service: The step service.
        study_service: The study service.
        user: Auth check.
        current_user: The current user details.

    Returns:
        The created content.
    """
    page = await page_service.get(page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        step = await step_service.get(page.study_step_id)
        if step:
            has_access = await study_service.check_study_access(step.study_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    content = await content_service.create_for_owner(page_id, new_content)
    return StudyStepPageContentRead.model_validate(content)


@router.patch('/{page_id}/contents/reorder', status_code=status.HTTP_204_NO_CONTENT)
async def reorder_page_contents(
    page_id: uuid.UUID,
    payload: list[ReorderPayloadSchema],
    content_service: StudyStepPageContentServiceDep,
    page_service: StudyStepPageServiceDep,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:content', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Reorder contents within a study step page.

    Args:
        page_id: The UUID of the page.
        payload: List of content IDs and new positions.
        content_service: The content service.
        page_service: The page service.
        step_service: The step service.
        study_service: The study service.
        user: Auth check.
        current_user: The current user details.

    Returns:
        Empty dictionary on success.
    """
    page = await page_service.get(page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        step = await step_service.get(page.study_step_id)
        if step:
            has_access = await study_service.check_study_access(step.study_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found.')

    contents_map = {item.id: item.order_position for item in payload}
    await content_service.reorder_items(page_id, contents_map)
