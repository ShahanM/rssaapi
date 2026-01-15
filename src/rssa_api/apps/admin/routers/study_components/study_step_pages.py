"""Router for managing study step pages in the admin API."""

import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import OrderedListItem
from rssa_api.data.schemas.study_components import (
    StudyStepPageContentCreate,
    StudyStepPageRead,
)
from rssa_api.data.services.dependencies import StudyStepPageContentServiceDep, StudyStepPageServiceDep

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
    user: Annotated[Auth0UserSchema, Depends(require_permissions('read:pages', 'admin:all'))],
):
    """Get details of a specific study step page.

    Args:
        page_id: The UUID of the page.
        page_service: The page service.
        user: Auth check.

    Returns:
        The study step page details.
    """
    page_from_db = await page_service.get_detailed(page_id, StudyStepPageRead)
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
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:pages', 'admin:all'))],
):
    """Update a study step page.

    Args:
        page_id: The UUID of the page to update.
        updated_page: Dictionary of fields to update.
        page_service: The page service.
        user: Auth check.

    Returns:
        Status message.
    """
    await page_service.update(page_id, updated_page)
    return {'status': 'success'}


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
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:pages', 'admin:all'))],
):
    """Delete a study step page.

    Args:
        page_id: The UUID of the page to delete.
        page_service: The page service.
        user: Auth check.

    Returns:
        Status message.
    """
    await page_service.delete(page_id)

    return {'status': 'success'}


@router.get(
    '/{page_id}/contents',
    response_model=list[OrderedListItem],
)
async def get_page_content(
    page_id: uuid.UUID,
    content_service: StudyStepPageContentServiceDep,
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('read:content', 'admin:all')),
    ],
):
    """Get content items associated with a page.

    Args:
        page_id: The UUID of the page.
        content_service: The page content service.
        user: Auth check.

    Returns:
        A list of ordered content items.
    """
    content = await content_service.get_items_for_owner_as_ordered_list(page_id)

    return [OrderedListItem.model_validate(c) for c in content]


@router.post(
    '/{page_id}/contents',
    status_code=status.HTTP_201_CREATED,
    response_model=Any,
)
async def add_content_to_page(
    page_id: uuid.UUID,
    new_content: StudyStepPageContentCreate,
    content_service: StudyStepPageContentServiceDep,
    _: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('create:content', 'admin:all')),
    ],
):
    """Add content to a study step page.

    Args:
        page_id: The UUID of the page.
        new_content: Data for the new content.
        content_service: The page content service.
        _: Auth check.

    Returns:
        Status and ID of created content.
    """
    content = await content_service.create_for_owner(page_id, new_content)
    # return StudyStepPageContentCreate.model_validate(content)
    return {'status': 'success', 'content_id': str(content.id)}
