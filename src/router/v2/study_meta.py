from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from datetime import datetime, timezone

from compute.utils import *
# from data.studydatabase import SessionLocal
from data.models.schemas.studyschema import *
from docs.metadata import TagsMetadataEnum as Tags

from .auth0 import get_current_user as auth0_user
from data.rssadb import get_db as rssadb

from data.logger import *
from data.accessors.studies import *
from data.accessors.survey_constructs import *

import uuid


router = APIRouter(prefix='/v2/meta')

# # Dependency
# def get_db():
# 	db = SessionLocal()
# 	try:
# 		yield db
# 	finally:
# 		db.close()

# base_path = lambda x: '/v2/meta' + x

@router.get(
	'/study/',
	response_model=List[StudySchema],
	tags=[Tags.meta])
async def retrieve_studies(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	studies = get_studies(db)
	log_access(db, current_user.sub, 'read', 'studies')

	return studies


@router.post(
	'/study/',
	response_model=StudySchema,
	tags=[Tags.meta])
async def new_study(new_study: CreateStudySchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):

	study = create_study(db, new_study.name, new_study.description)
	log_access(db, current_user.sub, 'create', 'study', str(study.id))
	study = StudySchema.model_validate(study)

	return study


@router.post(
	'/study/{study_id}',
	response_model=StudySchema,
	tags=[Tags.meta])
async def dupe_study(study_id: str, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	
	study = duplicate_study(db, uuid.UUID(study_id))
	log_access(db, current_user.sub, 'create', 'study', study.id)

	return study


@router.get(
	'/studycondition/{study_id}',
	response_model=List[StudyConditionSchema],
	tags=[Tags.meta])
async def retrieve_conditions(study_id: str, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	conditions = get_study_conditions(db, uuid.UUID(study_id))
	log_access(db, current_user.sub, 'read', 'conditions for study', study_id)

	return conditions


@router.post(
	'/studycondition/',
	response_model=StudyConditionSchema,
	tags=[Tags.meta])
async def new_condition(new_condition: CreateStudyConditionSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	condition = create_study_condition(db, new_condition.study_id, new_condition.name, new_condition.description)
	log_access(db, current_user.sub, 'create', 'condition', condition.id)

	return condition


@router.get(
	'/step/{study_id}',
	response_model=List[StudyStepSchema],
	tags=[Tags.meta])
async def retrieve_steps(
	study_id: str, db: Session = Depends(rssadb),
	current_user = Depends(auth0_user)):
	
	steps = get_study_steps(db, uuid.UUID(study_id))
	
	log_access(db, current_user.sub, 'read', 'steps for study', study_id)

	return steps


@router.post(
	'/step/',
	response_model=StudyStepSchema,
	tags=[Tags.meta])
async def new_step(new_step: CreateStepSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	step = create_study_step(db, **new_step.dict())
	log_access(db, current_user.sub, 'create', 'step', step.id)

	return step


@router.get(
	'/page/{step_id}',
	response_model=List[StepPageSchema],
	tags=[Tags.study])
async def retrieve_pages(step_id: str, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	pages = get_step_pages(db, uuid.UUID(step_id))
	
	log_access(db, current_user.sub, 'read', 'page for step', step_id)

	return pages


@router.post(
	'/page/',
	response_model=StepPageSchema,
	tags=[Tags.meta])
async def new_page(
	new_page: CreatePageSchema, db: Session = Depends(rssadb),
	current_user = Depends(auth0_user)):

	page = create_step_page(db, **new_page.dict())
	
	log_access(db, current_user.sub, 'create', 'page', page.id)

	return page


@router.get(
	'/pagecontent/{page_id}',
	response_model=List[SurveyConstructSchema],
	tags=[Tags.meta])
async def retrieve_page_content(
	page_id: str, db: Session = Depends(rssadb),
	current_user = Depends(auth0_user)):
	
	constructs = get_page_content(db, uuid.UUID(page_id))
	
	log_access(db, current_user.sub, 'read', 'page content', page_id)

	return constructs


@router.post('/pagecontent/', response_model=SurveyConstructSchema, tags=[Tags.meta])
async def attach_content_to_page(page_content: CreatePageContentSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	
	pcont = create_page_content(db, page_content.page_id, page_content.construct_id, page_content.order_position)
	construct = get_survey_construct_by_id(db, pcont.content_id)
	construct_type = get_construct_type_by_id(db, construct.type)
	
	construct_schema = SurveyConstructSchema(
		id=construct.id,
		name=construct.name,
		desc=construct.desc,
		type=construct_type,
		scale=construct.scale
	)
	# constructdeets = construct.__dict__
	# print(constructdeets)
	log_access(db, current_user.sub, 'create', 'page content', pcont.page_id)

	return construct_schema


"""
The following routes regarding constructs should be moved to a separate router file
"""
@router.get(
	'/construct/',
	response_model=List[SurveyConstructSchema],
	tags=[Tags.meta])
async def retrieve_constructs(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	constructs = get_survey_constructs(db)
	log_access(db, current_user.sub, 'read', 'constructs')

	return constructs


@router.post(
	'/construct/',
	response_model=SurveyConstructSchema,
	tags=[Tags.meta])
async def new_construct(new_construct: NewSurveyConstructSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	if new_construct.scale_id == '':
		construct = create_text_construct(db, new_construct.name, new_construct.desc, new_construct.type_id)
	else:
		construct = create_survey_construct(db, new_construct.name, new_construct.desc, new_construct.type_id, uuid.UUID(new_construct.scale_id))

	log_access(db, current_user.sub, 'create', 'construct', construct.id)

	return construct


@router.put(
	'/construct/{construct_id}',
	response_model=SurveyConstructSchema,
	tags=[Tags.meta])
async def update_construct(construct_id: str, updated_construct: UpdateSurveyConstructSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	
	update = update_survey_construct(db, uuid.UUID(construct_id), **updated_construct.dict())
	log_access(db, current_user.sub, 'update', 'construct', construct_id)

	return update


@router.get(
	'/construct/{construct_id}',
	response_model=SurveyConstructDetailSchema,
	tags=[Tags.meta])
async def retrieve_construct_details(construct_id: str, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	
	construct = get_survey_construct_by_id(db, uuid.UUID(construct_id))
	construct_type = None
	if construct.type:
		construct_type = get_construct_type_by_id(db, construct.type)
	construct_scale_deets = None
	if construct.scale:
		construct_scale = get_construct_scale_by_id(db, construct.scale)
		scale_levels = get_construct_scale_levels(db, construct.scale)
		construct_scale_deets = ConstructScaleDetailSchema(
			id=construct_scale.id,
			levels=construct_scale.levels,
			name=construct_scale.name,
			scale_levels=[ScaleLevelSchema(level=level.level, label=level.label, scale_id=level.scale_id) for level in scale_levels]
		)

	construct_deets = SurveyConstructDetailSchema(
		id=construct.id,
		name=construct.name,
		desc=construct.desc,
		type=ConstructTypeSchema.from_orm(construct_type) if construct_type else None,
		scale=construct_scale_deets,
		items=construct.items
	)
	
	log_access(db, current_user.sub, 'read', 'construct details', construct_id)

	return construct_deets


@router.get(
	'/constructtype/',
	response_model=List[ConstructItemTypeSchema],
	tags=[Tags.meta])
async def retrieve_construct_types(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	types = get_construct_types(db)
	log_access(db, current_user.sub, 'read', 'construct types')

	return types


@router.post('/constructtype/', response_model=ConstructTypeSchema, tags=[Tags.meta])
async def new_construct_type(new_type: NewConstructTypeSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	item_type = create_construct_type(db, new_type.type)
	log_access(db, current_user.sub, 'create', 'construct type', item_type.id)

	return item_type


@router.get('/constructscale/', response_model=List[ConstructScaleSchema], tags=[Tags.meta])
async def retrieve_construct_scales(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	scales = get_construct_scales(db)
	log_access(db, current_user.sub, 'read', 'construct scales')

	return scales


@router.post('/constructscale/', response_model=ConstructScaleSchema, tags=[Tags.meta])
async def new_construct_scale(new_scale: NewConstructScaleSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	scale = create_construct_scale(db, new_scale.levels, new_scale.name, new_scale.scale_levels)
	log_access(db, current_user.sub, 'create', 'construct scale', scale.id)
	return scale


@router.get('/item/{construct_id}', response_model=List[ConstructItemSchema], tags=[Tags.meta])
async def retrieve_construct_items(construct_id: str, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	items = get_construct_items(db, uuid.UUID(construct_id))
	log_access(db, current_user.sub, 'read', 'construct items', construct_id)

	return items


@router.post('/item/', response_model=ConstructItemSchema, tags=[Tags.meta])
async def new_construct_item(new_item: CreateConstructItemSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	item = create_construct_item(db, new_item.construct_id, new_item.item_type, new_item.text, new_item.order_position)
	log_access(db, current_user.sub, 'create', 'construct item', item.id)

	return item


@router.get('/itemtype/', response_model=List[ConstructItemTypeSchema], tags=[Tags.meta])
async def retrieve_construct_item_types(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	types = get_item_types(db)
	log_access(db, current_user.sub, 'read', 'construct item types')

	return types


@router.post('/itemtype/', response_model=ConstructItemTypeSchema, tags=[Tags.meta])
async def new_construct_item_type(new_type: NewConstructItemTypeSchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	item_type = create_item_type(db, new_type.type)
	log_access(db, current_user.sub, 'create', 'construct item type', item_type.id)

	return item_type
