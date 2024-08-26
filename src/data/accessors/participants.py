from typing import List, Union
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from ..models.schema.studyschema import NewScaleLevelSchema
from ..models.study_v2 import *
from ..models.survey_constructs import *
from ..models.participants import *

from .studies import get_study_by_id, get_study_conditions

from data.rssadb import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, and_, or_, select
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import HTTPException

import random


def get_participant_types(db: Session) -> List[ParticipantType]:
	types = db.query(ParticipantType).all()
	
	return types


def get_participant_type_by_id(db: Session, type_id: uuid.UUID) -> ParticipantType:
	ptype = db.query(ParticipantType).where(ParticipantType.id == type_id).first()
	if not ptype:
		raise HTTPException(status_code=404, detail='Participant type not found')
	
	return ptype


def create_participant_type(db: Session, type: str) -> ParticipantType:
	participant_type = ParticipantType(type=type)
	db.add(participant_type)
	db.commit()
	db.refresh(participant_type)

	return participant_type


def get_study_participants(db: Session, study_id: uuid.UUID) -> List[Participant]:
	participants = db.query(Participant).where(Participant.study_id == study_id).all()
	
	return participants


def get_study_participant_by_id(db: Session, participant_id: uuid.UUID) -> Participant:
	participant = db.query(Participant).where(Participant.id == participant_id).first()
	if not participant:
		raise HTTPException(status_code=404, detail='Participant not found')
	
	return participant


def create_study_participant(db: Session, study_id: uuid.UUID, 
		participant_type: uuid.UUID,
		external_id: str,
		current_step: uuid.UUID,
		current_page: Union[uuid.UUID, None] = None) -> Participant:
	
	study = get_study_by_id(db, study_id)
	study_conditions = get_study_conditions(db, study_id)

	if not study_conditions:
		raise HTTPException(status_code=404, detail='No study conditions found for study: ' + str(study.id))
	
	condition = random.choice(study_conditions)

	cstep = db.query(Step).where(Step.id == current_step).first()
	cpage = None
	if current_page is not None:
		cpage = db.query(Page).where(Page.id == current_page).first()
	ptype = get_participant_type_by_id(db, participant_type)
	participant = Participant(participant_type=ptype.id, study_id=study.id,
			condition_id=condition.id, current_step=cstep.id,
			external_id=external_id,
			current_page=cpage.id if cpage is not None else None)
	db.add(participant)
	db.commit()
	db.refresh(participant)

	return participant


def create_participant_response(db: Session, participant_id: UUID, construct_id: UUID,
		response: str, item_id: Union[UUID, None] = None) -> ParticipantResponse:
	partres = ParticipantResponse(participant_id=participant_id, construct_id=construct_id,
			response=response, item_id=item_id)
	db.add(response)
	db.commit()
	db.refresh(response)

	return partres

