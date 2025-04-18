import uuid
from datetime import datetime, timezone
from typing import Union

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from data.rssadb import Base


class ParticipantType(Base):
	__tablename__ = "participant_type"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type = Column(String, nullable=False)

	def __init__(self, type: str):
		self.type = type


class StudyParticipant(Base):
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


class ParticipantSurveyResponse(Base):
	__tablename__ = "participant_survey_response"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_id = Column(UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False)
	construct_id = Column(UUID(as_uuid=True), ForeignKey('survey_construct.id'), nullable=False)
	item_id = Column(UUID(as_uuid=True), ForeignKey('construct_item.id'), nullable=True)
	response = Column(String, nullable=False)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	date_modified = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	discarded = Column(Boolean, nullable=False, default=False)

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


class ParticipantResponse(Base):
    __tablename__ = "participant_response"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey('study_participant.id', ondelete='CASCADE'), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey('study_step.id', ondelete='CASCADE'), nullable=False)
    response = Column(JSONB, nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    date_modified = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    discarded = Column(Boolean, nullable=False, default=False)

    participant = relationship('StudyParticipant')
    step = relationship('Step')

    def __init__(self, participant_id: UUID, step_id: UUID, response: str):
        self.participant_id = participant_id
        self.step_id = step_id
        self.response = response


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


class Demographic(Base):
	__tablename__ = "demographics"

	participant_id = Column(UUID(as_uuid=True), ForeignKey('study_participant.id'), primary_key=True)
	age_range = Column(String, nullable=False)
	gender = Column(String, nullable=False)
	gender_other = Column(String, nullable=True)
	race = Column(String, nullable=False)
	race_other = Column(String, nullable=True)
	education = Column(String, nullable=False)
	country = Column(String, nullable=False)
	state_region = Column(String, nullable=True)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	date_updated = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	discarded = Column(Boolean, nullable=False, default=False)

	def __init__(self, participant_id: UUID, age_range: str, gender: str, race: str,\
		education: str, country: str, state_region: Union[str, None] = None,\
		gender_other: Union[str, None] = None, race_other: Union[str, None] = None):
		self.participant_id = participant_id
		self.age_range = age_range
		self.gender = gender
		self.gender_other = gender_other
		self.race = race
		self.race_other = race_other
		self.education = education
		self.country = country
		self.state_region = state_region
