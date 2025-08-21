import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from data.schemas.survey_construct_schemas import PageContentCreateSchema
from data.services import SurveyService
from data.services.rssa_dependencies import get_survey_service as survey_service
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2/admin/survey',
	tags=[Tags.study],
	dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.post('/', status_code=200)
async def link_survey_construct_to_page(
	new_survey_page: PageContentCreateSchema,
	service: Annotated[SurveyService, Depends(survey_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	await service.create_survey_page(new_survey_page)
