import uuid
from datetime import datetime, timezone
from typing import List, Optional, Union

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import RSSADBBase as Base
from data.models.survey_constructs import SurveyConstruct


class Study(Base):
	__tablename__ = 'study'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))

	created_by: Mapped[str] = mapped_column()
	owner: Mapped[Optional[str]] = mapped_column()

	name: Mapped[str] = mapped_column()
	description: Mapped[Optional[str]] = mapped_column()

	enabled: Mapped[bool] = mapped_column(default=True)

	steps: Mapped['Step'] = relationship('Step', back_populates='study', uselist=True, cascade='all, delete-orphan')
	conditions: Mapped['StudyCondition'] = relationship(
		'StudyCondition', back_populates='study', uselist=True, cascade='all, delete-orphan'
	)

	def __init__(self, name: str, created_by: str, description: Union[str, None] = None):
		self.name = name
		self.description = description
		self.created_by = created_by
		self.owner = created_by


class StudyCondition(Base):
	__tablename__ = 'study_condition'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)

	name: Mapped[str] = mapped_column()
	description: Mapped[Optional[str]] = mapped_column()

	recommendation_count: Mapped[int] = mapped_column(default=10)

	date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	enabled: Mapped[bool] = mapped_column(default=True)

	study: Mapped['Study'] = relationship('Study', back_populates='conditions')

	def __init__(self, study_id: uuid.UUID, name: str, rec_count: int = 10, description: Optional[str] = None):
		self.study_id = study_id
		self.name = name
		self.recommendation_count = rec_count
		self.description = description


class Step(Base):
	__tablename__ = 'study_step'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)

	order_position: Mapped[int] = mapped_column()
	name: Mapped[str] = mapped_column()
	description: Mapped[Optional[str]] = mapped_column()
	date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	enabled: Mapped[bool] = mapped_column(default=True)

	study: Mapped['Study'] = relationship('Study', back_populates='steps')
	pages: Mapped['Page'] = relationship('Page', back_populates='step', uselist=True, cascade='all, delete-orphan')

	def __init__(self, study_id: uuid.UUID, order_position: int, name: str, description: Optional[str] = None):
		self.study_id = study_id
		self.order_position = order_position
		self.name = name
		self.description = description


class PageContent(Base):
	__tablename__ = 'page_content'

	page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('step_page.id'), primary_key=True)
	content_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('survey_construct.id'), primary_key=True
	)
	order_position: Mapped[int] = mapped_column()
	enabled: Mapped[bool] = mapped_column(default=True)

	page: Mapped['Page'] = relationship('Page', back_populates='page_contents')
	survey_construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='page_contents')

	def __init__(self, page_id: uuid.UUID, content_id: uuid.UUID, order_position: int):
		self.page_id = page_id
		self.content_id = content_id
		self.order_position = order_position


class Page(Base):
	__tablename__ = 'step_page'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)
	step_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_step.id'), nullable=False)

	order_position: Mapped[int] = mapped_column()
	name: Mapped[str] = mapped_column()
	description: Mapped[Optional[str]] = mapped_column()
	date_created: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
	enabled: Mapped[bool] = mapped_column(default=True)

	step: Mapped['Step'] = relationship('Step', back_populates='pages')

	page_contents: Mapped[List[PageContent]] = relationship(
		'PageContent', back_populates='page', uselist=True, cascade='all, delete-orphan'
	)

	def __init__(
		self,
		study_id: uuid.UUID,
		step_id: uuid.UUID,
		order_position: int,
		name: str,
		description: Optional[str] = None,
	):
		self.study_id = study_id
		self.step_id = step_id
		self.order_position = order_position
		self.name = name
		self.description = description
