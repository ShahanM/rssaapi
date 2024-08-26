from typing import List, Union
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from data.rssadb import Base


class ParticipantType(Base):
	__tablename__ = "participant_type"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type = Column(String, nullable=False)

	def __init__(self, type: str):
		self.type = type


class Participant(Base):
	__tablename__ = "study_participant"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_type = Column(UUID(as_uuid=True), ForeignKey('participant_type.id'), nullable=False)
	external_id = Column(String, nullable=True)
	study_id = Column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)
	condition_id = Column(UUID(as_uuid=True), ForeignKey('study_condition.id'), nullable=False)
	current_status = Column(String, nullable=False)
	current_step = Column(UUID(as_uuid=True), ForeignKey('study_step.id'), nullable=False)
	current_page = Column(UUID(as_uuid=True), ForeignKey('step_page.id'), nullable=True)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	date_updated = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	discarded = Column(Boolean, nullable=False, default=False)

	# ptype = relationship('ParticipantType', uselist=False)

	def __init__(self, participant_type: UUID, study_id: UUID, condition_id: UUID,
			external_id: str,
			current_step: UUID, current_page: Union[UUID, None] = None):
		self.participant_type = participant_type
		self.study_id = study_id
		self.condition_id = condition_id
		self.current_status = 'active'
		self.external_id = external_id
		self.current_step = current_step
		self.current_page = current_page


class ParticipantResponse(Base):
	__tablename__ = "participant_response"

	participant_id = Column(UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False)
	construct_id = Column(UUID(as_uuid=True), ForeignKey('survey_construct.id'), nullable=False)
	item_id = Column(UUID(as_uuid=True), ForeignKey('construct_item.id'), nullable=True)
	response = Column(String, nullable=False)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	discarded = Column(Boolean, nullable=False, default=False)

	PrimaryKeyConstraint(participant_id, construct_id, item_id)

	def __init__(self, participant_id: UUID, construct_id: UUID, response: str, item_id: Union[UUID, None] = None):
		self.participant_id = participant_id
		self.construct_id = construct_id
		self.response = response
		self.item_id = item_id


class ParticipantContentRating(Base):
	__tablename__ = "participant_content_rating"

	participant_id = Column(UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False)
	content_id = Column(UUID(as_uuid=True), nullable=False)
	content_type = Column(String, nullable=False)
	rating = Column(Integer, nullable=False)
	scale_min = Column(Integer, nullable=False)
	scale_max = Column(Integer, nullable=False)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

	PrimaryKeyConstraint(participant_id, content_type, content_id)

	def __init__(self, participant_id: UUID, content_type: str, content_id: UUID, rating: int, scale_min: int, scale_max: int):
		self.participant_id = participant_id
		self.content_type = content_type
		self.content_id = content_id
		self.rating = rating
		self.scale_min = scale_min
		self.scale_max = scale_max


class ParticipantInteractionLog(Base):
	__tablename__ = "participant_interaction_log"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_id = Column(UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False)
	action = Column(String, nullable=False)
	action_data = Column(JSON, nullable=True)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

	def __init__(self, participant_id: UUID, action: str, action_data: Union[str, None] = None):
		self.participant_id = participant_id
		self.action = action
		self.action_data = action_data

