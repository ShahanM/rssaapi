import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.step_page_schemas import StepPageCreateSchema, StepPageSchema
from data.schemas.survey_schemas import SurveyPageSchema
from data.services.step_page_service import StepPageService
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.resources.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2/admin',
	tags=[Tags.study],
	dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.post('/pages/', status_code=201)
async def create_step_page(
	new_page: StepPageCreateSchema,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	page_service = StepPageService(db)
	await page_service.create_step_page(new_page)


@router.get('/pages/{page_id}', response_model=SurveyPageSchema)
async def get_step_page_details(
	page_id: uuid.UUID,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	page_service = StepPageService(db)
	page_from_db = await page_service.get_page_with_content_detail(page_id)

	return SurveyPageSchema.model_validate(page_from_db)
