import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.study_components import StudyStepPageContentUpdate
from rssa_api.data.services import StudyStepPageContentServiceDep

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
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:content'))],
):
    await service.delete(content_id)

    return {}


@router.patch('/{content_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_page_content(
    content_id: uuid.UUID,
    payload: StudyStepPageContentUpdate,
    service: StudyStepPageContentServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:content', 'admin:all'))],
):
    await service.update(content_id, payload.model_dump(exclude_unset=True))
    return {'status': 'success'}
