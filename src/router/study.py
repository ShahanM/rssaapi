from typing import List

from fastapi import APIRouter, Depends, Request, HTTPException, status
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


def study_authorized_token(request: Request) -> str:
	study_id = request.headers.get('X-Study-Id')
	if not study_id:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST, 
			detail='Application request not registered for a study'
		)
	return study_id


def get_current_registered_study(request: Request) -> Study:
	study_id = study_authorized_token(request)
	study = get_study_by_id(next(rssadb()), uuid.UUID(study_id))
	
	return study



@router.get(base_path('/study/'), response_model=StudyAuthSchema, tags=[Tags.study, Tags.admin])
async def retrieve_studies(db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):
	log_access(db, f'study: {current_study.name} ({current_study.id})', 'app access', 'study')

	return current_study



@router.get(base_path('/studystep/first'), response_model=StudyStepSchema, tags=[Tags.study])
async def retrieve_first_step(db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):
	step = get_first_step(db, current_study.id)
	log_access(db, f'study: {current_study.name} ({current_study.id})', 'read', 'first step')

	return step


@router.post(base_path('/studystep/next'), response_model=StudyStepSchema, tags=[Tags.study])
async def retrieve_next_step(step_req: StepIdRequestSchema, db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):
	step = get_next_step(db, current_study.id, current_step_id=step_req.current_step_id)
	if not step:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, 
			detail='No next step found'
		)
	log_access(db, f'study: {current_study.name} ({current_study.id})', 'read', 'next step')

	return step


@router.get(base_path('/survey/{step_id}/first'), response_model=SurveyPageSchema, tags=[Tags.study])
async def retrieve_survey_page(step_id: uuid.UUID, db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):
	page = get_first_survey_page(db, step_id)
	if not page:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, 
			detail='No survey page found'
		)
	
	construct = get_page_content(db, page.id)
	if len(construct) == 0:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, 
			detail='No construct found for survey page'
		)
	construct = construct[0] # FIXME: We currently only support one construct per page
	items = get_construct_items(db, construct.id)
	scalelevels = get_construct_scale_levels(db, construct.scale)

	survey = SurveyPageSchema(
		step_id=page.step_id,
		page_id=page.id,
		order_position=page.order_position,
		construct_id=construct.id,
		construct_items=[ConstructItemSchema.from_orm(item) for item in items],
		construct_scale=[ScaleLevelSchema.from_orm(level) for level in scalelevels]
	)

	log_access(db, f'study: {current_study.name} ({current_study.id})', 'read', f'survey page {page.id}')

	return survey


@router.get(base_path('/survey/{page_id}'), response_model=SurveyPageSchema, tags=[Tags.study])
async def retrieve_survey_page_by_id(page_id: uuid.UUID, db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):
	
	page = get_survey_page(db, page_id)
	if not page:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, 
			detail='No survey page found'
		)

	constructs = get_page_content(db, page.id)
	if len(constructs) == 0:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, 
			detail='No construct found for survey page'
		)
	
	construct = constructs[0] # FIXME: We currently only support one construct per page
	items = get_construct_items(db, construct.id)
	assert construct.scale is not None
	scalelevels = get_construct_scale_levels(db, construct.scale)

	survey = SurveyPageSchema(
		step_id=page.step_id,
		page_id=page.id,
		order_position=0,
		construct_id=construct.id,
		construct_items=[ConstructItemSchema.from_orm(item) for item in items],
		construct_scale=sorted([ScaleLevelSchema.from_orm(level) for level in scalelevels], key=lambda x: x.level)
	)

	log_access(db, f'study: {current_study.name} ({current_study.id})', 'read', f'survey page {page.id}')
	
	return survey


@router.get(base_path('/page/{page_id}'), response_model=PageMultiConstructSchema, tags=[Tags.study])
async def retrieve_page_content(page_id: uuid.UUID, db: Session = Depends(rssadb),
					current_study = Depends(get_current_registered_study)):
	page = get_survey_page(db, page_id)
	if not page:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, 
			detail='No page found'
		)
	
	constructs = get_page_content(db, page.id)
	if len(constructs) == 0:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, 
			detail='No construct found for page'
		)
	
	page_constructs = []
	for construct in constructs:
		print(construct)
		items = get_construct_items(db, construct.id)
		print(items)
		constructdetail = TextConstructSchema(
			id=construct.id,
			name=construct.name,
			desc=construct.desc,
			type=construct.type.id,
			items=ConstructItemSchema.from_orm(items[0])
		)
		page_constructs.append(constructdetail)
	
	multipage = PageMultiConstructSchema(
		page_id=page.id,
		step_id=page.step_id,
		order_position=page.order_position,
		constructs=page_constructs
	)
	
	log_access(db, f'study: {current_study.name} ({current_study.id})', 'read', f'page content {page.id}')
	
	return multipage




# class SurveyPageSchema(BaseModel):
# 	step_id: uuid.UUID
# 	page_id: uuid.UUID
# 	order_position: int
# 	construct_id: uuid.UUID
# 	construct_items: List[ConstructItemSchema]
# 	construct_scale: ConstructScaleDetailSchema