from typing import List, Union
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, and_, or_, select
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from data.rssadb import Base


class Study(Base):
	__tablename__ = 'study'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

	name = Column(String, nullable=False)
	description = Column(String, nullable=True)

	enabled = Column(Boolean, nullable=False, default=True)

	steps = relationship('Step', back_populates='study', \
		uselist=True, cascade='all, delete-orphan')
	conditions = relationship('StudyCondition', back_populates='study', \
		uselist=True, cascade='all, delete-orphan')
	
	def __init__(self, name: str, description: Union[str, None] = None):
		self.name = name
		self.description = description


class StudyCondition(Base):
	__tablename__ = 'study_condition'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id = Column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)

	name = Column(String, nullable=False)
	description = Column(String, nullable=True)

	recommendation_count = Column(Integer, nullable=False, default=10)

	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	enabled = Column(Boolean, nullable=False, default=True)

	study = relationship('Study', back_populates='conditions')

	def __init__(self, study_id: UUID, name: str, study_condition: int = 10, \
		description: Union[str, None] = None):
		self.study_id = study_id
		self.name = name
		self.description = description


class Step(Base):
	__tablename__ = 'study_step'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id = Column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)
	
	order_position = Column(Integer, nullable=False)
	name = Column(String, nullable=False)
	description = Column(String, nullable=True)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	enabled = Column(Boolean, nullable=False, default=True)

	study = relationship('Study', back_populates='steps')
	pages = relationship('Page', back_populates='step', \
		uselist=True, cascade='all, delete-orphan')

	def __init__(self, study_id: UUID, order_position: int, name: str, description: Union[str, None] = None):
		self.study_id = study_id
		self.order_position = order_position
		self.name = name
		self.description = description


class Page(Base):
	__tablename__ = 'step_page'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id = Column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)
	step_id = Column(UUID(as_uuid=True), ForeignKey('study_step.id'), nullable=False)

	order_position = Column(Integer, nullable=False)
	name = Column(String, nullable=False)
	description = Column(String, nullable=True)
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	enabled = Column(Boolean, nullable=False, default=True)

	step = relationship('Step', back_populates='pages')

	def __init__(self, study_id: UUID, step_id: UUID, order_position: int,
			name: str, description: Union[str, None] = None):
		self.study_id = study_id
		self.step_id = step_id
		self.order_position = order_position
		self.name = name
		self.description = description


class PageContent(Base):
	__tablename__ = 'page_content'

	page_id = Column(UUID(as_uuid=True), ForeignKey('step_page.id'), primary_key=True)
	content_id = Column(UUID(as_uuid=True), ForeignKey('survey_construct.id'), primary_key=True)
	order_position = Column(Integer, nullable=False)
	enabled = Column(Boolean, nullable=False, default=True)

	def __init__(self, page_id: UUID, content_id: UUID, order_position: int):
		self.page_id = page_id
		self.content_id = content_id
		self.order_position = order_position


class Feedback(Base):
	__tablename__ = 'feedback'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_id = Column(UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False)
	created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
	updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
	study_id = Column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)
	feedback = Column(String, nullable=False)
	feedback_type = Column(String, nullable=False)
	feedback_category = Column(String, nullable=False)

	def __init__(self, participant_id: UUID, study_id: UUID, feedback: str, feedback_type: str, feedback_category: str):
		self.participant_id = participant_id
		self.study_id = study_id
		self.feedback = feedback
		self.feedback_type = feedback_type
		self.feedback_category = feedback_category