from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.study_schemas import StudyAuthSchema, StudySchema
from data.schemas.study_step_schemas import NextStepRequest, StudyStepSchema
from data.services.study_service import StudyService
from docs.metadata import TagsMetadataEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

router = APIRouter(
	prefix='/v2',
	tags=[Tags.study.value],
)


@router.get('/study/', response_model=StudyAuthSchema)
async def retrieve_study(
	db: AsyncSession = Depends(rssa_db), current_study: StudySchema = Depends(get_current_registered_study)
):
	"""Get the current registered study"""

	return current_study


@router.get('/study/step/first', response_model=StudyStepSchema)
async def retrieve_first_step(
	db: AsyncSession = Depends(rssa_db), current_study: StudySchema = Depends(get_current_registered_study)
):
	study_service = StudyService(db)
	study_step = await study_service.get_first_step(current_study.id)

	return study_step


@router.post('/study/step/next', response_model=StudyStepSchema)
async def retrieve_next_step(
	step_request: NextStepRequest,
	db: AsyncSession = Depends(rssa_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	study_service = StudyService(db)
	study_step = await study_service.get_next_step(current_study.id, step_request.current_step_id)

	return study_step
