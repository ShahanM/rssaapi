import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services import SurveyScaleLevelServiceDep

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
):
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
        )

    await service.delete_scale_level(level_id)
