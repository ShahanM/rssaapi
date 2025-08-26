import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from data.schemas.study_schemas import StudyAuthSchema, StudySchema
from data.schemas.study_step_schemas import NextStepRequest, StudyStepSchema
from data.services import StudyService
from data.services.rssa_dependencies import get_study_service as study_service
from docs.metadata import ResourceTagsEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/studies',
	tags=[Tags.study],
	dependencies=[Depends(get_current_registered_study)],
)


@router.get('/', response_model=StudyAuthSchema)
async def get_study(current_study: Annotated[StudySchema, Depends(get_current_registered_study)]):
	return current_study


@router.get('/steps/first', response_model=StudyStepSchema)
async def get_first_step(
	study_service: Annotated[StudyService, Depends(study_service)],
	current_study: Annotated[StudySchema, Depends(get_current_registered_study)],
):
	study_step = await study_service.get_first_step(current_study.id)

	return StudyStepSchema.model_validate(study_step)


@router.post('/steps/next', response_model=StudyStepSchema)
async def get_next_step(
	step_request: NextStepRequest,
	study_service: Annotated[StudyService, Depends(study_service)],
	current_study: Annotated[StudySchema, Depends(get_current_registered_study)],
):
	study_step = await study_service.get_next_step(current_study.id, step_request.current_step_id)

	return study_step
