import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.step_page_schemas import StepPageSchema
from data.schemas.study_step_schemas import StudyStepDetailSchema
from data.services.study_step_service import StudyStepService
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.resources.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
	prefix='/v2/admin',
	tags=[Tags.study_step],
)


@router.get('/steps/{study_step_id}', response_model=StudyStepDetailSchema)
async def get_study_step(
	study_step_id: uuid.UUID,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	step_service = StudyStepService(db)
	step_in_db = await step_service.get_study_step_with_pages(study_step_id)

	return StudyStepDetailSchema.model_validate(step_in_db)


@router.get('/steps/{study_step_id}/pages', response_model=List[StepPageSchema])
async def get_pages_for_study_step(
	study_step_id: uuid.UUID,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	step_service = StudyStepService(db)
	pages_from_db = await step_service.get_pages_for_step(study_step_id)

	return [StepPageSchema.model_validate(p) for p in pages_from_db]
