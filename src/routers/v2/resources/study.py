import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.study_schemas import StudyAuthSchema, StudySchema
from data.schemas.study_step_schemas import NextStepRequest, StudyStepSchema
from data.services.study_service import StudyService
from docs.metadata import TagsMetadataEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2',
	tags=[Tags.study],
	dependencies=[Depends(get_current_registered_study)],
)


@router.get('/study/', response_model=StudyAuthSchema)
async def retrieve_study(current_study: Annotated[StudySchema, Depends(get_current_registered_study)]):
	"""_summary_

	Args:
		db (AsyncSession, optional): _description_. Defaults to Depends(rssa_db).
		current_study (StudySchema, optional): _description_. Defaults to Depends(get_current_registered_study).

	Returns:
		_type_: _description_
	"""

	return current_study


@router.get('/study/step/first', response_model=StudyStepSchema)
async def retrieve_first_step(
	db: Annotated[AsyncSession, Depends(rssa_db)],
	current_study: Annotated[StudySchema, Depends(get_current_registered_study)],
):
	"""_summary_

	Args:
		db (AsyncSession, optional): _description_. Defaults to Depends(rssa_db).
		current_study (StudySchema, optional): _description_. Defaults to Depends(get_current_registered_study).

	Returns:
		_type_: _description_
	"""
	study_service = StudyService(db)
	study_step = await study_service.get_first_step(current_study.id)

	return study_step


@router.post('/study/step/next', response_model=StudyStepSchema)
async def retrieve_next_step(
	step_request: NextStepRequest,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	current_study: Annotated[StudySchema, Depends(get_current_registered_study)],
):
	"""_summary_

	Args:
		step_request (NextStepRequest): _description_
		db (AsyncSession, optional): _description_. Defaults to Depends(rssa_db).
		current_study (StudySchema, optional): _description_. Defaults to Depends(get_current_registered_study).

	Returns:
		_type_: _description_
	"""
	study_service = StudyService(db)
	study_step = await study_service.get_next_step(current_study.id, step_request.current_step_id)

	return study_step
