import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_auth0_authenticated_user, require_permissions
from data.schemas import Auth0UserSchema
from data.services import SurveyService
from data.services.rssa_dependencies import get_survey_service as survey_service
from docs.admin_docs import Tags

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
    prefix='/contents',
    tags=[Tags.survey],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.delete('/{content_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_survey_construct_from_page(
    content_id: uuid.UUID,
    service: Annotated[SurveyService, Depends(survey_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:page_content'))],
):
    await service.delete_construct_from_page(content_id)

    return {}
