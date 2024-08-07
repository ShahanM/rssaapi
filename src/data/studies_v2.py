from typing import List, Union
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from data.rssadb import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, and_, or_
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid


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
	date_created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
	enabled = Column(Boolean, nullable=False, default=True)

	study = relationship('Study', back_populates='conditions')

	def __init__(self, study_id: UUID, name: str):
		self.study_id = study_id
		self.name = name


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


class AccessLog(Base):
	__tablename__ = 'access_log'
	
	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	auth0_user = Column(String, nullable=False)
	action = Column(String, nullable=False)
	resource = Column(String, nullable=False)
	resource_id = Column(String, nullable=True)
	timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

	def __init__(self, auth0_user: str, action: str, resource: str, resource_id: Union[str, None] = None):
		self.auth0_user = auth0_user
		self.action = action
		self.resource = resource
		self.resource_id = resource_id


class SurveyConstruct(Base):
	__tablename__ = "survey_construct"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	name = Column(String, nullable=False)
	desc = Column(String, nullable=False)

	items = relationship('ConstructItem', back_populates='construct', \
		uselist=True, cascade='all, delete-orphan')

	def __init__(self, name: str, desc: str):
		self.name = name
		self.desc = desc


class ConstructItemType(Base):
	__tablename__ = "construct_item_type"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type = Column(String, nullable=False)

	def __init__(self, type: str):
		self.type = type


class ConstructItem(Base):
	__tablename__ = "construct_item"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	construct_id = Column(UUID(as_uuid=True), ForeignKey('survey_construct.id'), nullable=False)
	text = Column(String, nullable=False)
	order_position = Column(Integer, nullable=False)
	item_type = Column(UUID(as_uuid=True), ForeignKey('construct_item_type.id'), nullable=False)

	construct = relationship('SurveyConstruct', back_populates='items')

	def __init__(self, construct_id: UUID, text: str, order_position: int, item_type: UUID):
		self.construct_id = construct_id
		self.text = text
		self.order_position = order_position
		self.item_type = item_type


def create_study(db: Session, name: str, description: str) -> Study:
	study = Study(name=name, description=description)
	db.add(study)
	db.commit()
	db.refresh(study)

	return study


def get_studies(db: Session) -> List[Study]:
	# FIXME: This should query based on access control
	studies = db.query(Study).all()
	
	return studies


def get_study_steps(db: Session, study_id: uuid.UUID) -> List[Step]:
	steps = db.query(Step).where(Step.study_id == study_id).all()

	return steps


def create_study_step(db: Session, study_id: UUID, order_position: int,
		name: str, description: str) -> Step:
	study = db.query(Study).where(Study.id == study_id).first()
	if not study:
		raise Exception('Study not found')
	
	step = Step(study_id=study.id, order_position=order_position, name=name,
			description=description)
	db.add(step)
	db.commit()
	db.refresh(step)

	return step


def get_step_pages(db: Session, step_id: uuid.UUID) -> List[Page]:
	# FIXME: check if we should filter by sutdy_id too
	pages = db.query(Page)\
		.where(and_(Page.step_id == step_id)).all()

	return pages


def create_step_page(db: Session, study_id: UUID, step_id: UUID,\
	order_position: int, name: str, description: str) -> Page:
	step = db.query(Step).where(Step.id == step_id).first()
	if not step:
		raise Exception('Step not found')
	
	page = Page(study_id=study_id, step_id=step_id, order_position=order_position,
			name=name, description=description)
	db.add(page)
	db.commit()
	db.refresh(page)

	return page


def create_survey_construct(db: Session, name: str, desc: str) -> SurveyConstruct:
	construct = SurveyConstruct(name=name, desc=desc)
	db.add(construct)
	db.commit()
	db.refresh(construct)

	return construct


def create_construct_item_type(db: Session, type: str) -> ConstructItemType:
	item_type = ConstructItemType(type=type)
	db.add(item_type)
	db.commit()
	db.refresh(item_type)

	return item_type


def create_construct_item(db: Session, construct_id: UUID, text: str,
		order_position: int, item_type: UUID) -> ConstructItem:
	item = ConstructItem(construct_id=construct_id, text=text,
			order_position=order_position, item_type=item_type)
	db.add(item)
	db.commit()
	db.refresh(item)

	return item


def log_access(db: Session, auth0user: str, action: str, resource: str,
		resource_id: Union[str, None] = None) -> None:
	log = AccessLog(auth0_user=auth0user, action=action, resource=resource,
			resource_id=resource_id)
	db.add(log)
	db.commit()
	db.refresh(log)
