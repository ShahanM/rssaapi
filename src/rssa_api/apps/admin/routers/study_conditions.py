import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.study_components import StudyConditionBaseSchema
from rssa_api.data.services import StudyConditionService
from rssa_api.data.services.rssa_dependencies import get_study_condition_service as conditions_service

from ..docs import ADMIN_STUDY_CONDITIONS_TAG

router = APIRouter(
    prefix='/conditions',
    tags=[ADMIN_STUDY_CONDITIONS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user), Depends(conditions_service)],
)


@router.get('/{condition_id}', response_model=StudyConditionBaseSchema)
async def get_item(
    condition_id: uuid.UUID,
    service: Annotated[StudyConditionService, Depends(conditions_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
):
    condition = await service.get_study_condition(condition_id)
    if condition is None:
        raise (HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.'))

    return condition
