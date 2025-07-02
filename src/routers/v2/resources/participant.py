from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.participant_schemas import (
	DemographicsCreateSchema,
	ParticipantCreateSchema,
	ParticipantSchema,
	ParticipantUpdateSchema,
)
from data.schemas.study_schemas import StudySchema
from data.services.participant_service import ParticipantService
from data.services.participant_session_service import ParticipantSessionService
from docs.metadata import ResourceTagsEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

router = APIRouter(prefix='/v2', tags=[Tags.participant], dependencies=[Depends(get_current_registered_study)])


@router.post('/participants/', response_model=ParticipantSchema)
async def create_study_participant(
	new_participant: ParticipantCreateSchema,
	db: Annotated[AsyncSession, Depends(rssa_db)],
):
	"""_summary_

	Args:
		new_participant (ParticipantCreateSchema): _description_
		db (Annotated[AsyncSession, Depends): _description_

	Returns:
		_type_: _description_
	"""
	participant_service = ParticipantService(db)
	session_service = ParticipantSessionService(db)

	new_participant = await participant_service.create_study_participant(new_participant)

	print(new_participant.id)

	movie_subset = 'ers'  # FIXME: This should be parameter in the study that defines the segment of items to include
	await session_service.assign_pre_shuffled_list_participant(new_participant.id, movie_subset)

	await db.commit()

	return ParticipantSchema.model_validate(new_participant)


@router.put('/participants/', response_model=ParticipantSchema)
async def update_participant(
	participant_data: ParticipantUpdateSchema,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	current_study: Annotated[StudySchema, Depends(get_current_registered_study)],
):
	"""_summary_

	Args:
		participant_data (ParticipantUpdateSchema): _description_
		db (Annotated[AsyncSession, Depends): _description_
		current_study (Annotated[StudySchema, Depends): _description_

	Raises:
		HTTPException: _description_

	Returns:
		_type_: _description_
	"""
	if current_study.id != participant_data.study_id:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED, detail='There are no records of the participant in the study.'
		)
	participant_service = ParticipantService(db)
	updated = await participant_service.update_study_participant(participant_data)

	return updated


@router.post('/participants/demographics', response_model=None)
async def create_particpant_demographic_info(
	demographic_data: DemographicsCreateSchema,
	db: Annotated[AsyncSession, Depends(rssa_db)],
):
	"""_summary_

	Args:
		demographic_data (DemographicsCreateSchema): _description_
		db (Annotated[AsyncSession, Depends): _description_
	"""
	participant_service = ParticipantService(db)
	await participant_service.create_or_update_demographic_info(demographic_data)
