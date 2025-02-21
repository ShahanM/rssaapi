from typing import List, Union
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..models.schema.studyschema import (
    NewScaleLevelSchema, SurveyConstructSchema,
    StudyConditionSchema,
	ConstructTypeSchema, PageContentSchema, StudySchema, StepPageSchema
)

from ..models.study_v2 import *
from ..models.survey_constructs import *

from data.rssadb import Base
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, and_, or_, select
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import HTTPException


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


def get_study_by_id(db: Session, study_id: uuid.UUID) -> StudySchema:
	study = db.query(Study).where(Study.id == study_id).first()
	
	return study


def duplicate_study(db: Session, study_id: uuid.UUID) -> Study:
	study = get_study_by_id(db, study_id)
	if not study:
		raise Exception('Study not found')
	
	copy_name = f'{study.name} (copy)'
	new_study = Study(name=copy_name, description=study.description)
	db.add(new_study)
	db.commit()

	new_study = StudySchema.model_validate(new_study)
	# Duplicate conditions
	conditions = get_study_conditions(db, study_id)
	for condition in conditions:
		_ = create_study_condition(db, new_study.id, condition.name, condition.description)
	
	# Duplicate steps
	steps = get_study_steps(db, study_id)
	for step in steps:
		_ = create_study_step(db, new_study.id, step.order_position, step.name, step.description)

		# Duplicate pages
		pages = get_step_pages(db, step.id)
		for page in pages:
			_ = create_step_page(db, new_study.id, step.id, page.order_position, page.name, page.description)

			# Duplicate page content
			contents = get_page_content(db, page.id)
			for content in contents:
				_ = create_page_content(db, page.id, content.id, content.order_position)

	return new_study


def get_study_conditions(db: Session, study_id: uuid.UUID) -> List[StudyConditionSchema]:
	conditions = db.query(StudyCondition).where(StudyCondition.study_id == study_id).all()
	
	return conditions


def get_study_condition(db: Session, condition_id: uuid.UUID) -> StudyCondition:
	condition = db.query(StudyCondition).where(StudyCondition.id == condition_id).first()
	
	return condition


def create_study_condition(db: Session, study_id: uuid.UUID, name: str, description: str) -> StudyCondition:
	study = db.query(Study).where(Study.id == study_id).first()
	if not study:
		raise Exception('Study not found')
	
	condition = StudyCondition(study_id=study.id, name=name, description=description)
	db.add(condition)
	db.commit()
	db.refresh(condition)

	return condition


def get_study_steps(db: Session, study_id: uuid.UUID) -> List[Step]:
	steps = db.query(Step).where(Step.study_id == study_id).all()
	
	return steps


def get_first_step(db: Session, study_id: uuid.UUID) -> Step:
	step = db.query(Step).where(Step.study_id == study_id).order_by(Step.order_position).first()
	
	return step


def get_next_step(db: Session, study_id: uuid.UUID, current_step_id: uuid.UUID) -> Union[Step, None]:
	current = db.query(Step).where(Step.id == current_step_id).first()
	steps = db.query(Step).where(and_(Step.study_id == study_id, Step.order_position > current.order_position))
	if steps.count() == 0:
		# No more steps
		return None
	step = steps.first()
	
	return step


def create_study_step(db: Session, study_id: uuid.UUID, order_position: int,
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


def create_step_page(db: Session, study_id: uuid.UUID, step_id: uuid.UUID,\
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


def get_page_content(db: Session, page_id: uuid.UUID) -> List[SurveyConstructSchema]:
	query = select(SurveyConstruct, ConstructType)\
		.join(PageContent, SurveyConstruct.id == PageContent.content_id)\
		.join(ConstructType, SurveyConstruct.type == ConstructType.id)\
		.where(PageContent.page_id == page_id)
	# constructs = db.query(SurveyConstruct)\
	# 	.join(SurveyConstruct, )\
	# 	.join(ConstructType)\
	# 	.where(PageContent.page_id == page_id).all()
	constructs = db.execute(query).all()
	# query = select(SurveyConstruct, ConstructType)\
	
	svyconstructs: List[SurveyConstructSchema] = []
	for construct in constructs:
		svyconstruct = construct[0]
		construct_type = construct[1]
		svyconstructs.append(SurveyConstructSchema(id=svyconstruct.id, name=svyconstruct.name,
				desc=svyconstruct.desc, type=construct_type, scale=svyconstruct.scale))

	# return svyconstructs
	return svyconstructs


def create_page_content(db: Session, page_id: uuid.UUID, content_id: uuid.UUID,
		order_position: int) -> PageContentSchema:
	page = db.query(Page).where(Page.id == page_id).first()
	if not page:
		raise Exception('Page not found')

	page = StepPageSchema.model_validate(page)
	
	content = db.query(SurveyConstruct).where(SurveyConstruct.id == content_id).first()
	if not content:
		raise Exception('Content not found')

	content = SurveyConstructSchema.model_validate(content)
	
	# Check to see if the content is already in the page
	existing = db.query(PageContent).where(and_(PageContent.page_id == page_id,
			PageContent.content_id == content_id)).first()

	if existing:
		return existing
	
	page_content = PageContent(page_id=page.id, content_id=content.id, order_position=order_position)
	db.add(page_content)
	db.commit()
	db.refresh(page_content)

	return page_content


def get_first_survey_page(db: Session, step_id: uuid.UUID) -> StepPageSchema:
	page = db.query(Page).filter(Page.step_id == step_id).order_by(Page.order_position).first()
	
	return page


def get_survey_page(db: Session, page_id: uuid.UUID) -> Page:
	page = db.query(Page).where(Page.id == page_id).first()
	
	return page