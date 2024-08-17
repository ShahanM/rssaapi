from typing import List, Union
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..models.schema.studyschema import NewScaleLevelSchema
from ..models.study_v2 import *
from ..models.survey_constructs import *
from ..models.participants import *

from data.rssadb import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, and_, or_, select
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import HTTPException


def get_participant_types(db: Session) -> List[ParticipantType]:
	types = db.query(ParticipantType).all()
	
	return types


def create_participant_type(db: Session, type: str) -> ParticipantType:
	participant_type = ParticipantType(type=type)
	db.add(participant_type)
	db.commit()
	db.refresh(participant_type)

	return participant_type


def get_study_participants(db: Session, study_id: uuid.UUID) -> List[Participant]:
	participants = db.query(Participant).where(Participant.study_id == study_id).all()
	
	return participants


def create_study_participant(db: Session, participant_type: UUID, study_id: UUID,
		condition_id: UUID, current_step: UUID,
		current_page: Union[UUID, None] = None) -> Participant:
	participant = Participant(participant_type=participant_type, study_id=study_id,
			condition_id=condition_id, current_step=current_step,
			current_page=current_page)
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

