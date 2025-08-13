import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from data.schemas.study_schemas import StudySchema
from data.schemas.survey_schemas import SurveyPageSchema
from data.services import SurveyService
from data.services import get_survey_service as survey_service
from docs.metadata import ResourceTagsEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
	prefix='/v2',
	tags=[Tags.survey],
	dependencies=[Depends(get_current_registered_study)],
)


@router.get('/surveys/{step_id}/first', response_model=SurveyPageSchema)
async def get_first_page_endpoint(
	step_id: uuid.UUID,
	service: Annotated[SurveyService, Depends(survey_service)],
):
	first_page = await service.get_first_survey_page(step_id)
	if not first_page:
		raise HTTPException(status_code=404, detail='No first page found for this step or step not in study.')

	is_last_page = await service.is_last_page_in_step(first_page)
	page_to_return = SurveyPageSchema.model_validate(first_page)
	page_to_return.last_page = is_last_page

	return page_to_return


@router.get('/surveys/{step_id}/pages/{current_page_id}/next', response_model=SurveyPageSchema)
async def get_next_page_endpoint(
	current_page_id: uuid.UUID,
	service: Annotated[SurveyService, Depends(survey_service)],
	current_study: Annotated[StudySchema, Depends(get_current_registered_study)],
):
	next_page = await service.get_next_survey_page(current_study.id, current_page_id)

	if not next_page:
		raise HTTPException(
			status_code=404, detail='No next page found for this current page or page not found in study/step.'
		)

	is_last_page = await service.is_last_page_in_step(next_page)
	page_to_return = SurveyPageSchema.model_validate(next_page)
	page_to_return.last_page = is_last_page

	return page_to_return
