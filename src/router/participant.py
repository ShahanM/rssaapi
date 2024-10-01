from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from datetime import datetime, timezone

from compute.utils import *
from data.studydatabase import SessionLocal
from data.models.schema.studyschema import *
from data.models.schema.participanschema import *
from docs.metadata import TagsMetadataEnum as Tags

from .auth0 import get_current_user as auth0_user
from data.rssadb import get_db as rssadb
from .study import get_current_registered_study

from data.studies_v2 import *
from data.accessors.studies import *
from data.accessors.survey_constructs import *
from data.accessors.participants import *
from data.accessors.study_responses import *

import uuid


router = APIRouter()

# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

base_path = lambda x: '/api/v2' + x


@router.get(base_path('/meta/participanttype/'), response_model=List[ParticipantTypeSchema], tags=[Tags.admin])
async def retrieve_participant_types(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	types = get_participant_types(db)
	log_access(db, current_user.sub, 'read', 'participant types')

	return types


@router.post(base_path('/meta/participanttype/'), response_model=ParticipantTypeSchema, tags=[Tags.admin])
async def new_participant_type(new_type: NewParticipantTypeSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):

	participant_type = create_participant_type(db, new_type.type)
	log_access(db, current_user.sub, 'create', 'participant type', participant_type.id)
	participant_type = ParticipantTypeSchema.from_orm(participant_type)

	return participant_type


@router.post(base_path('/participant/'), response_model=ParticipantSchema, tags=[Tags.study])
async def new_study_participant(new_participant: NewParticipantSchema, db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):

	participant = create_study_participant(db, study_id=new_participant.study_id, 
		participant_type=new_participant.participant_type,
		external_id=new_participant.external_id,
		current_step=new_participant.current_step,
		current_page=new_participant.current_page)

	log_access(db, f'study: {current_study.name} ({current_study.id})', 'create', 'participant', participant.id)

	return participant


@router.put(base_path('/participant/'), response_model=bool, tags=[Tags.study])
async def update_participant(participant: ParticipantSchema, db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):
	
	current = get_study_participant_by_id(db, participant.id)
	current = ParticipantSchema.from_orm(current)
	diff = current.diff(participant)

	log_access(db, f'study: {current_study.name} ({current_study.id})', 'update', 'participant', ';'.join(diff))

	return True
	

@router.post(base_path('/participant/{participant_id}/response/'), response_model=bool, tags=[Tags.study])
async def new_participant_response(participant_id: uuid.UUID, response: SurveyResponse, db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):

	success = create_survey_response(db, participant_id, response)
	log_access(db, f'study: {current_study.name} ({current_study.id})', 'create', 'response', str(participant_id))

	return success