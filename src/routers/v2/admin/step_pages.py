import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from data.schemas.step_page_schemas import StepPageCreateSchema
from data.schemas.survey_schemas import SurveyPageSchema
from data.services import StepPageService
from data.services.rssa_dependencies import get_step_page_service as page_service
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
	prefix='/v2/admin',
	tags=[Tags.study],
	dependencies=[Depends(get_auth0_authenticated_user), Depends(page_service)],
)


@router.post('/pages/', status_code=201)
async def create_step_page(
	new_page: StepPageCreateSchema,
	page_service: Annotated[StepPageService, Depends(page_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	await page_service.create_step_page(new_page)


@router.get('/pages/{page_id}', response_model=SurveyPageSchema)
async def get_step_page_details(
	page_id: uuid.UUID,
	page_service: Annotated[StepPageService, Depends(page_service)],
):
	page_from_db = await page_service.get_page_with_content_detail(page_id)

	return SurveyPageSchema.model_validate(page_from_db)


@router.put('/pages/{page_id}', status_code=201)
async def update_step_page(
	page_id: uuid.UUID,
	updated_page: dict[str, str],
	page_service: Annotated[StepPageService, Depends(page_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	await page_service.update_step_page(page_id, updated_page)
