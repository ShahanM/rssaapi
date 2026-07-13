"""Admin router for survey construct items."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.survey_components import SurveyItemRead
from rssa_api.data.services.dependencies import SurveyItemServiceDep

from ...docs import ADMIN_CONSTRUCT_ITEMS_TAG

router = APIRouter(
    prefix='/items',
    tags=[ADMIN_CONSTRUCT_ITEMS_TAG],
    dependencies=[
        Depends(get_auth0_authenticated_user),
        Depends(require_permissions('read:items', 'admin:all')),
    ],
)


@router.get('/{item_id}/', response_model=SurveyItemRead)
async def get_item(
    item_id: uuid.UUID,
    service: SurveyItemServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:items', 'admin:all'))],
) -> SurveyItemRead:
    """Retrieve a survey construct item by its ID."""
    item_in_db = await service.get(item_id, SurveyItemRead)

    return SurveyItemRead.model_validate(item_in_db)


@router.patch('/{item_id}')
@router.patch(
    '/{item_id}/',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Update a survey item.',
    description="""Updates an existing survey item with the provided fields.""",
    response_description='HTTP 204 NO CONTENT on success.',
)
async def update_item(
    item_id: uuid.UUID,
    payload: dict[str, Any],
    service: SurveyItemServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('update:items', 'admin:all'))],
) -> None:
    """Update a survey item."""
    await service.update(item_id, payload)


@router.delete(
    '/{item_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete a survey item.',
    description="""Deletes a survey item by its ID.""",
    response_description='HTTP 204 NO CONTENT on success.',
)
async def delete_construct_item(
    item_id: uuid.UUID,
    service: SurveyItemServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('delete:items', 'admin:all'))],
) -> None:
    """Delete a survey item."""
    await service.delete(item_id)
