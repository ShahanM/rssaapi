"""Router for managing study authorizations by ID."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import (
    get_auth0_authenticated_user,
    require_permissions,
)
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.study_components import StudyAuthorizationRead
from rssa_api.data.services.dependencies import StudyAuthorizationServiceDep

from ...docs import ADMIN_STUDIES_TAG

router = APIRouter(
    prefix='/studies',
    tags=[ADMIN_STUDIES_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get(
    '/authorizations/{authorization_id}',
    response_model=StudyAuthorizationRead,
    summary='Get a study authorization by ID.',
    description="""
    Get details of a specific authorization record.

    ## Permissions
    Requires: `admin:all`
    """,
)
async def get_study_authorization(
    authorization_id: uuid.UUID,
    service: StudyAuthorizationServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
) -> StudyAuthorizationRead:
    """Get a study authorization by ID."""
    auth = await service.get_one(authorization_id)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Authorization not found',
        )
    return StudyAuthorizationRead.model_validate(auth)


@router.delete(
    '/authorizations/{authorization_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete a study authorization.',
    description="""
    Delete a specific authorization record.

    ## Permissions
    Requires: `admin:all`
    """,
)
async def delete_study_authorization(
    authorization_id: uuid.UUID,
    service: StudyAuthorizationServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
) -> None:
    """Delete a study authorization."""
    existing = await service.get_one(authorization_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Authorization not found',
        )
    await service.delete(authorization_id)
