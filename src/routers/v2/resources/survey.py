import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.study_schemas import StudySchema
from data.schemas.survey_schemas import SurveyPageSchema
from data.services.survey_service import SurveyService
from docs.metadata import TagsMetadataEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

router = APIRouter(
	prefix='/v2',
	tags=[Tags.study],
)


@router.get('/survey/{step_id}/first', response_model=SurveyPageSchema)
async def get_first_page_endpoint(
	step_id: uuid.UUID,
	db: AsyncSession = Depends(rssa_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	survey_service = SurveyService(db)
	first_page = await survey_service.get_first_survey_page(step_id)
	if not first_page:
		raise HTTPException(status_code=404, detail='No first page found for this step or step not in study.')

	is_last_page = await survey_service.is_last_page_in_step(first_page)
	page_to_return = SurveyPageSchema.model_validate(first_page)
	page_to_return.last_page = is_last_page

	return page_to_return


@router.get('/survey/{step_id}/page/{current_page_id}/next', response_model=SurveyPageSchema)
async def get_next_page_endpoint(
	current_page_id: uuid.UUID,
	db: AsyncSession = Depends(rssa_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	survey_service = SurveyService(db)
	next_page = await survey_service.get_next_survey_page(current_study.id, current_page_id)

	if not next_page:
		raise HTTPException(
			status_code=404, detail='No next page found for this current page or page not found in study/step.'
		)

	is_last_page = await survey_service.is_last_page_in_step(next_page)
	page_to_return = SurveyPageSchema.model_validate(next_page)
	page_to_return.last_page = is_last_page

	return page_to_return
