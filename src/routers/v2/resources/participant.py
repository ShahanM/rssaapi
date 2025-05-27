import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from compute.utils import *
from data.models.schemas.studyschema import *
from data.repositories.participant import ParticipantRepository
from data.repositories.study_responses import *
from data.repositories.survey_constructs import *
from data.rssadb import get_db as rssa_db
from data.schemas.participant_schemas import ParticipantCreateSchema, ParticipantSchema, ParticipantUpdateSchema
from data.services.participant_service import ParticipantService
from docs.metadata import TagsMetadataEnum as Tags

from .auth0 import get_current_user as auth0_user
from .study import get_current_registered_study

router = APIRouter(prefix='/v2')


@router.post('/participant/', response_model=ParticipantSchema, tags=[Tags.participant])
async def new_study_participant(new_participant: ParticipantCreateSchema, db: AsyncSession = Depends(rssa_db)):
	participant_service = ParticipantService(db)
	participant = await participant_service.create_study_participant(new_participant)

	return participant


@router.put('/participant/', response_model=ParticipantSchema, tags=[Tags.participant])
async def update_participant(
	participant_data: ParticipantUpdateSchema,
	db: AsyncSession = Depends(rssa_db),
	current_study=Depends(get_current_registered_study),
):
	if current_study.id != participant_data.study_id:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED, detail='There are no records of the participant in the study.'
		)
	participant_service = ParticipantService(db)
	updated = await participant_service.update_study_participant(participant_data)

	return updated


def get_participant_repository(
	db: AsyncSession = Depends(rssa_db), study: Study = Depends(get_current_registered_study)
) -> ParticipantRepository:
	"""
	Dependency to get the participant repository
	"""
	return ParticipantRepository(db, study)


@router.get(
	'/meta/participanttype/',
	response_model=List[ParticipantTypeSchema],
	summary='Retrieve all participant types',
	tags=[Tags.meta],
)
async def retrieve_participant_types(db: Session = Depends(rssa_db), current_user=Depends(auth0_user)):
	types = get_participant_types(db)

	return types


@router.post('/meta/participanttype/', response_model=ParticipantTypeSchema, tags=[Tags.meta])
async def new_participant_type(
	new_type: NewParticipantTypeSchema, db: Session = Depends(rssa_db), current_user=Depends(auth0_user)
):
	participant_type = create_participant_type(db, new_type.type)

	if not participant_type:
		return False

	participant_type = ParticipantTypeSchema.model_validate(participant_type)

	return participant_type


@router.post('/participant/{participant_id}/surveyresponse/', response_model=bool, tags=[Tags.participant])
async def new_survey_response(
	participant_id: uuid.UUID,
	response: SurveyResponse,
	db: Session = Depends(rssa_db),
	current_study=Depends(get_current_registered_study),
):
	success = create_survey_response(db, participant_id, response)
	log_access(db, f'study: {current_study.name} ({current_study.id})', 'create', 'response', str(participant_id))

	return success


@router.post('/participant/{participant_id}/textresponse/', response_model=bool, tags=[Tags.participant])
async def new_text_response(
	participant_id: uuid.UUID,
	response: GroupedTextResponse,
	db: Session = Depends(rssa_db),
	current_study=Depends(get_current_registered_study),
):
	page_id = response.page_id

	success = False
	if len(response.responses) > 1:
		success = batch_create_text_responses(db, participant_id, response.responses)
	else:
		success = create_text_response(db, participant_id, response.responses[0])

	# FIXME: The log order calls are wrong for all expect this one
	# Fix the others: participant_id, action, resource, resource_id
	log_access(
		db,
		str(participant_id),
		'create',
		'response',
		f'study: {current_study.name} ({current_study.id}): page {page_id}',
	)

	return success


@router.post('/participant/{participant_id}/demographics/', response_model=bool, tags=[Tags.participant])
async def new_demographics(
	participant_id: uuid.UUID,
	demographics: DemographicSchema,
	db: Session = Depends(rssa_db),
	current_study=Depends(get_current_registered_study),
):
	print('demographics: ', participant_id, demographics)
	success = create_participant_demographic(db, participant_id, demographics)

	log_access(db, f'study: {current_study.name} ({current_study.id})', 'create', 'demographics', str(participant_id))

	return success


@router.post('/participant/{participant_id}/feedback/', response_model=bool, tags=[Tags.participant])
async def new_feedback(
	participant_id: uuid.UUID,
	feedback: FeedbackSchema,
	db: Session = Depends(rssa_db),
	current_study=Depends(get_current_registered_study),
):
	success = create_feedback(db, participant_id, feedback.feedback, feedback.feedback_type, feedback.feedback_category)
	log_access(db, f'study: {current_study.name} ({current_study.id})', 'create', 'feedback', str(participant_id))

	return success
