import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import RSSADBBase as Base
from data.models.survey_constructs import ConstructScale, SurveyConstruct


class Study(Base):
	__tablename__ = 'study'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	date_created: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)

	created_by: Mapped[str] = mapped_column()
	owner: Mapped[Optional[str]] = mapped_column()

	name: Mapped[str] = mapped_column()
	description: Mapped[Optional[str]] = mapped_column()

	enabled: Mapped[bool] = mapped_column(default=True)

	steps: Mapped[List['Step']] = relationship(
		'Step', back_populates='study', uselist=True, cascade='all, delete-orphan', order_by='Step.order_position'
	)
	conditions: Mapped[List['StudyCondition']] = relationship(
		'StudyCondition', back_populates='study', uselist=True, cascade='all, delete-orphan'
	)


class StudyCondition(Base):
	__tablename__ = 'study_condition'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)

	name: Mapped[str] = mapped_column()
	description: Mapped[Optional[str]] = mapped_column()

	recommendation_count: Mapped[int] = mapped_column(default=10)

	date_created: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	enabled: Mapped[bool] = mapped_column(default=True)

	study: Mapped['Study'] = relationship('Study', back_populates='conditions')


class Step(Base):
	__tablename__ = 'study_step'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)

	order_position: Mapped[int] = mapped_column()
	name: Mapped[str] = mapped_column()
	description: Mapped[Optional[str]] = mapped_column()

	title: Mapped[Optional[str]] = mapped_column()
	instructions: Mapped[Optional[str]] = mapped_column()

	step_type: Mapped[Optional[str]] = mapped_column('step_type', nullable=True)

	date_created: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	enabled: Mapped[bool] = mapped_column(default=True)

	study: Mapped['Study'] = relationship('Study', back_populates='steps')
	pages: Mapped[List['Page']] = relationship(
		'Page', back_populates='step', uselist=True, cascade='all, delete-orphan'
	)

	__table_args__ = (
		UniqueConstraint(
			'study_id',
			'order_position',
			name='study_step_study_id_order_position_key',
			deferrable=True,
			initially='deferred',
		),
	)


class PageContent(Base):
	__tablename__ = 'page_content'
	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('step_page.id'), primary_key=True)
	content_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('survey_construct.id'), primary_key=True
	)
	scale_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('construct_scale.id'), primary_key=True)
	order_position: Mapped[int] = mapped_column()
	enabled: Mapped[bool] = mapped_column(default=True)

	page: Mapped['Page'] = relationship('Page', back_populates='page_contents')
	survey_construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='page_contents')
	construct_scale: Mapped['ConstructScale'] = relationship('ConstructScale', back_populates='page_contents')


class Page(Base):
	__tablename__ = 'step_page'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)
	step_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_step.id'), nullable=False)

	order_position: Mapped[int] = mapped_column()
	name: Mapped[str] = mapped_column()
	description: Mapped[Optional[str]] = mapped_column()

	title: Mapped[Optional[str]] = mapped_column()
	instructions: Mapped[Optional[str]] = mapped_column()

	page_type: Mapped[Optional[str]] = mapped_column('page_type', nullable=True)

	date_created: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	enabled: Mapped[bool] = mapped_column(default=True)

	step: Mapped['Step'] = relationship('Step', back_populates='pages')

	page_contents: Mapped[List[PageContent]] = relationship(
		'PageContent', back_populates='page', uselist=True, cascade='all, delete-orphan'
	)
