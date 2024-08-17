from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from datetime import datetime, timezone

from compute.utils import *
from data.studydatabase import SessionLocal
from data.models.schema.studyschema import *
from docs.metadata import TagsMetadataEnum as Tags

from .auth0 import get_current_user as auth0_user
from data.rssadb import get_db as rssadb

from data.studies_v2 import *
from data.accessors.studies import *
from data.accessors.survey_constructs import *
from data.accessors.participants import *

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


@router.get(base_path('/participanttype/'), response_model=List[ParticipantTypeSchema], tags=[Tags.admin])
async def retrieve_participant_types(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	types = get_participant_types(db)
	log_access(db, current_user.sub, 'read', 'participant types')

	return types


@router.post(base_path('/participanttype/'), response_model=ParticipantTypeSchema, tags=[Tags.admin])
async def new_participant_type(new_type: NewParticipantTypeSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):

	participant_type = create_participant_type(db, new_type.type)
	log_access(db, current_user.sub, 'create', 'participant type', participant_type.id)
	participant_type = ParticipantTypeSchema.from_orm(participant_type)

	return participant_type


@router.post(base_path('/participant/'), response_model=ParticipantSchema, tags=[Tags.study])
async def new_study_participant(new_participant: NewParticipantSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):

	# participant = create_study_participant(db, new_participant.participant_type,
	# 		new_participant.study_id, new_participant.condition_id,
	# 		new_participant.current_step, new_participant.current_page)
	# log_access(db, current_user.sub, 'create', 'participant', participant.id)
	# participant = ParticipantSchema.from_orm(participant)

	participant = ParticipantSchema(
		id=uuid.uuid4(),
		participant_type=new_participant.participant_type,
		external_id=new_participant.external_id,
		study_id=uuid.UUID('fc5ced48-dcbd-42b2-9f78-83f19eb4398b'),
		condition_id=uuid.UUID(''),
		current_step=new_participant.current_step,
		current_page=new_participant.current_page)

	return participant