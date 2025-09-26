import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_auth0_authenticated_user, require_permissions
from data.schemas import Auth0UserSchema
from data.schemas.survey_constructs import (
    ScaleLevelBaseSchema,
    ScaleLevelSchema,
)
from data.services import ScaleLevelService
from data.services.survey_dependencies import get_scale_level_service as scale_level_service
from docs.admin_docs import Tags

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
    prefix='/scale-levels',
    tags=[Tags.levels],
    dependencies=[Depends(get_auth0_authenticated_user), Depends(scale_level_service)],
)


@router.delete('/{level_id}', status_code=204)
async def delete_scale_level(
    service: Annotated[ScaleLevelService, Depends(scale_level_service)],
    level_id: uuid.UUID,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
        )

    await service.delete_scale_level(level_id)
