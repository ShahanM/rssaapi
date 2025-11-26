"""Admin router for survey construct items."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.survey_constructs import ConstructItemSchema
from rssa_api.data.services import SurveyItemServiceDep

from ...docs import ADMIN_CONSTRUCT_ITEMS_TAG

router = APIRouter(
    prefix='/items',
    tags=[ADMIN_CONSTRUCT_ITEMS_TAG],
    dependencies=[
        Depends(get_auth0_authenticated_user),
        Depends(require_permissions('read:constructs')),
    ],
)


@router.get('/{item_id}', response_model=ConstructItemSchema)
async def get_item(
    item_id: uuid.UUID,
    service: SurveyItemServiceDep,
):
    """Retrieve a survey construct item by its ID.

    Args:
        item_id: The UUID of the construct item to retrieve.
        service: The SurveyItemService dependency.

    Returns:
        The ConstructItemSchema representing the requested item.
    """
    item_in_db = await service.get_construct_item(item_id)

    return ConstructItemSchema.model_validate(item_in_db)


@router.delete('/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_construct_item(
    item_id: uuid.UUID,
    service: SurveyItemServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    """Deletes a survey construct item by its ID.

    Args:
        item_id: The UUID of the construct item to delete.
        service: The SurveyItemService dependency.
        user: The authenticated user performing the deletion.

    Raises:
        HTTPException: If the user does not have sufficient permissions.

    Returns:
        An empty response with HTTP 204 status code upon successful deletion.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
        )
    await service.delete_construct_item(item_id)

    return {'status': 'success'}
