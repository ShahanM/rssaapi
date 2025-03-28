from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.utils import *
# from data.studydatabase import SessionLocal
from data.models.schemas.studyschema import *
from data.models.schemas.participantschema import *
from docs.metadata import TagsMetadataEnum as Tags

from .auth0 import get_current_user as auth0_user
from data.rssadb import get_db as rssadb
from .study import get_current_registered_study

from data.logger import *
from data.accessors.studies import *
from data.accessors.survey_constructs import *
from data.accessors.participants import *
from data.accessors.study_responses import *

import uuid


router = APIRouter(prefix="/v2")


def get_participant_repository(
	db: Session = Depends(rssadb),
	study_id: uuid.UUID = Depends(get_current_registered_study)) -> ParticipantRepository:
	"""
	Dependency to get the participant repository
	"""
	return ParticipantRepository(db, study_id)


@router.get(
		'/meta/participanttype/',
		response_model=List[ParticipantTypeSchema],
		summary='Retrieve all participant types',
		tags=[Tags.meta])
async def retrieve_participant_types(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	types = get_participant_types(db)

	log_access(
		db,
		current_user.sub,
		'read',
		'participant types')

	return types


@router.post(
		'/meta/participanttype/',
		response_model=ParticipantTypeSchema,
		tags=[Tags.meta])
async def new_participant_type(new_type: NewParticipantTypeSchema,
		db: Session = Depends(rssadb), current_user = Depends(auth0_user)):
	
	participant_type = create_participant_type(db, new_type.type)

	if not participant_type:
		return False
	
	log_access(
		db,
		current_user.sub, 
		'create', 
		'participant type',
		participant_type.id)
	participant_type = ParticipantTypeSchema.model_validate(participant_type)

	return participant_type


# @router.post(
# 	'/participant/',
# 	response_model=ParticipantSchema,
# 	tags=[Tags.participant])
# async def new_study_participant(new_participant: NewParticipantSchema,
# 		db: Session = Depends(rssadb), 
# 		current_study = Depends(get_current_registered_study)):

# 	participant = create_study_participant(db,
# 		study_id=new_participant.study_id, 
# 		participant_type=new_participant.participant_type,
# 		external_id=new_participant.external_id,
# 		current_step=new_participant.current_step,
# 		current_page=new_participant.current_page)

# 	log_access(db, f'study: {current_study.name} ({current_study.id})',
# 		'create', 'participant', participant.id)

# 	return participant


@router.post(
	'/participant/',
	response_model=ParticipantSchema,
	tags=[Tags.participant])
async def new_study_participant(new_participant: NewParticipantSchema,
		repo: ParticipantRepository = Depends(get_participant_repository)):

	participant = repo.create_study_participant(
		participant_type=new_participant.participant_type,
		external_id=new_participant.external_id,
		current_step=new_participant.current_step,
		current_page=new_participant.current_page)

	# log_access(db, f'study: {current_study.name} ({current_study.id})',
	# 	'create', 'participant', participant.id)

	return participant


@router.put(
	'/participant/', 
	response_model=bool, 
	tags=[Tags.participant])
async def update_participant(participant: ParticipantSchema,
		db: Session = Depends(rssadb),
		current_study = Depends(get_current_registered_study)):
	
	current = get_study_participant_by_id(db, participant.id)
	current = ParticipantSchema.model_validate(current)
	diff = current.diff(participant)

	log_access(db, f'study: {current_study.name} ({current_study.id})',
		'update', 'participant', ';'.join(diff))

	return True
	

@router.post(
	'/participant/{participant_id}/surveyresponse/',
	response_model=bool,
	tags=[Tags.participant])
async def new_survey_response(participant_id: uuid.UUID,
		response: SurveyResponse, db: Session = Depends(rssadb),
		current_study = Depends(get_current_registered_study)):

	success = create_survey_response(db, participant_id, response)
	log_access(db, f'study: {current_study.name} ({current_study.id})',
		'create', 'response', str(participant_id))

	return success


@router.post(
	'/participant/{participant_id}/textresponse/',
	response_model=bool,
	tags=[Tags.participant])
async def new_text_response(participant_id: uuid.UUID, response: GroupedTextResponse,
		db: Session = Depends(rssadb),
		current_study = Depends(get_current_registered_study)):

	page_id = response.page_id

	success = False
	if (len(response.responses) > 1):
		success = batch_create_text_responses(db, participant_id,\
					response.responses)
	else:
		success = create_text_response(db, participant_id, response.responses[0])

	# FIXME: The log order calls are wrong for all expect this one
	# Fix the others: participant_id, action, resource, resource_id
	log_access(db, str(participant_id), 'create', 'response',
			f'study: {current_study.name} ({current_study.id}): page {page_id}')

	return success


@router.post(
	'/participant/{participant_id}/demographics/',
	response_model=bool,
	tags=[Tags.participant])
async def new_demographics(participant_id: uuid.UUID,
		demographics: DemographicSchema, db: Session = Depends(rssadb),
		current_study = Depends(get_current_registered_study)):

	print('demographics: ', participant_id, demographics)
	success = create_participant_demographic(db, participant_id, demographics)
	
	log_access(db, f'study: {current_study.name} ({current_study.id})',
		'create', 'demographics', str(participant_id))

	return success


@router.post(
	'/participant/{participant_id}/feedback/',
	response_model=bool,
	tags=[Tags.participant])
async def new_feedback(participant_id: uuid.UUID, feedback: FeedbackSchema,
		db: Session = Depends(rssadb),
		current_study = Depends(get_current_registered_study)):

	success = create_feedback(db, participant_id, feedback.feedback,
		feedback.feedback_type, feedback.feedback_category)
	log_access(db, f'study: {current_study.name} ({current_study.id})',
		'create', 'feedback', str(participant_id))

	return success