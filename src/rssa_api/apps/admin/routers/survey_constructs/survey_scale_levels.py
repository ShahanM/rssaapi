"""Router for managing survey scale levels in the admin API."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import SurveyScaleLevelServiceDep

from ...docs import ADMIN_SCALE_LEVELS_TAG

router = APIRouter(
    prefix='/levels',
    tags=[ADMIN_SCALE_LEVELS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.delete('/{level_id}', status_code=204)
async def delete_scale_level(
    service: SurveyScaleLevelServiceDep,
    level_id: uuid.UUID,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
) -> None:
    """Delete a scale level.

    Args:
        service: The scale level service.
        level_id: The UUID of the level to delete.
        user: The authenticated user.

    Raises:
        HTTPException: If the user lacks permissions.
        HTTPException: If the user lacks permissions.

    Returns:
        Empty dictionary on success.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
        )

    await service.delete(level_id)


@router.patch('/{level_id}', status_code=204)
async def update_scale_level(
    level_id: uuid.UUID,
    updated_level: dict[str, str | int],
    service: SurveyScaleLevelServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
) -> None:
    """Update a scale level.

    Args:
        level_id: The UUID of the level to update.
        updated_level: Dictionary of fields to update.
        service: The scale level service.
        user: The authenticated user.

    Raises:
        HTTPException: If the user lacks permissions.
        HTTPException: If the level is not found.

    Returns:
        Empty dictionary on success.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
        )

    await service.update(level_id, updated_level)
