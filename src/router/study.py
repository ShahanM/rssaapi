from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from datetime import datetime, timezone

from compute.utils import *
from data.studydatabase import SessionLocal
from data.models.schema.studyschema import *
from data.studies import *
from .admin import get_current_active_user, AdminUser
from docs.metadata import TagsMetadataEnum as Tags

from .auth0 import get_current_user as auth0_user
from data.rssadb import get_db as rssadb

from data.studies_v2 import \
	create_study as create_study_v2, get_studies as get_studies_v2, \
	create_study_step as create_study_step_v2, get_study_steps as get_study_steps_v2, \
	get_step_pages as get_step_pages_v2, create_step_page as create_step_page_v2, \
	log_access

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

# FIXME: udpate the function name
@router.get(base_path('/study/'), response_model=List[StudySchemaV2], tags=[Tags.study])
async def new_studies(db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	studies = get_studies_v2(db)
	log_access(db, current_user.sub, 'read', 'studies')

	return studies


@router.post(base_path('/study/'), response_model=StudySchemaV2, tags=[Tags.study, Tags.admin])
async def new_study(new_study: NewStudySchema, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):

	study = create_study_v2(db, new_study.study_name, new_study.study_description)
	log_access(db, current_user.sub, 'create', 'study', study.id)
	study = StudySchemaV2.from_orm(study)

	return study

# FIXME: update the function name
@router.get(base_path('/step/{study_id}'), response_model=List[StudyStepSchemaV2], tags=[Tags.step, Tags.study])
async def new_steps(study_id: str, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	
	steps = get_study_steps_v2(db, uuid.UUID(study_id))
	log_access(db, current_user.sub, 'read', 'steps for study', study_id)

	return steps


@router.post('/v2/{study_id}/step/', response_model=StudyStepSchemaV2, tags=[Tags.step, Tags.study])
async def new_step(new_step: NewStepSchemaV2, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	step = create_study_step_v2(db, **new_step.dict())
	log_access(db, current_user.sub, 'create', 'step', step.id)

	return step


@router.get(base_path('/page/{step_id}'), response_model=List[StepPageSchemaV2], tags=[Tags.page, Tags.study])
async def new_pages(step_id: str, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):
	pages = get_step_pages_v2(db, uuid.UUID(step_id))
	log_access(db, current_user.sub, 'read', 'page for step', step_id)

	return pages


@router.post('/v2/{study_id}/{step_id}/page/', response_model=StepPageSchemaV2, tags=[Tags.page, Tags.study])
async def new_page(new_page: NewPageSchemaV2, db: Session = Depends(rssadb),
					current_user = Depends(auth0_user)):

	page = create_step_page_v2(db, **new_page.dict())
	log_access(db, current_user.sub, 'create', 'page', page.id)

	return page





















@DeprecationWarning
@router.post('/study/', response_model=StudySchema, tags=[Tags.study, Tags.admin])
async def create_new_study(studyname: str, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	study = create_study(db=db, studyname=studyname)

	return study


@DeprecationWarning
@router.get('/study/', response_model=List[StudySchema], tags=[Tags.study])
async def get_all_studies(db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	studies = get_studies(db)

	return studies


@DeprecationWarning
@router.get('/study/{study_id}', response_model=StudySchema, tags=[Tags.study])
async def get_study(study_id: int, db: Session = Depends(get_db)):
	study = get_study_by_id(db, study_id)

	return study


@router.put('/study/{study_id}', response_model=StudySchema, tags=[Tags.study, Tags.admin])
async def update_study_details(study_id: int, study_name: str, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	study = update_study(db=db, study_id=study_id, study_name=study_name)

	return study


@router.delete('/study/{study_id}', response_model=StudySchema, tags=[Tags.study, Tags.admin])
async def delete_study(study_id: int, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	study = delete_study_by_id(db, study_id)

	return study















"""
Condition routes
"""
@router.post('/study/{study_id}/condition/', response_model=StudyConditionSchema, tags=[Tags.condition, Tags.admin])
async def create_new_condition(study_id: int, condition: NewConditionSchema, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	condition = create_study_condition(db=db, study_id=study_id, **condition.dict())

	return condition


@router.get('/study/{study_id}/condition/', response_model=List[StudyConditionSchema], tags=[Tags.condition])
async def get_all_conditions(study_id: int, db: Session = Depends(get_db)):
	conditions = get_study_conditions(db, study_id)

	return conditions


@router.get('/study/{study_id}/condition/{condition_id}', response_model=StudyConditionSchema, tags=[Tags.condition])
async def get_condition(study_id: int, condition_id: int, db: Session = Depends(get_db)):
	condition = get_study_condition_by_id(db, study_id, condition_id)

	return condition


@router.get('/study/{study_id}/condition/random/', response_model=StudyConditionSchema, tags=[Tags.condition])
async def get_random_condition(study_id: int, db: Session = Depends(get_db)):
	condition = get_random_study_condition(db, study_id)

	return condition


@router.put('/study/{study_id}/condition/{condition_id}', response_model=StudyConditionSchema, tags=[Tags.condition, Tags.admin])
async def update_condition(study_id: int, condition_id: int, condition: NewConditionSchema, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	condition = update_study_condition(db=db, study_id=study_id, condition_id=condition_id, **condition.dict())

	return condition


@router.delete('/study/{study_id}/condition/{condition_id}', response_model=StudyConditionSchema, tags=[Tags.condition, Tags.admin])
async def delete_condition(study_id: int, condition_id: int, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	condition = delete_study_condition(db=db, study_id=study_id, condition_id=condition_id)

	return condition


"""
Step routes
"""
@router.post('/study/{study_id}/step/', response_model=StepSchema, tags=[Tags.step, Tags.admin])
async def create_new_step(study_id: int, step: NewStepSchema, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	step = create_study_step(db=db, study_id=study_id, **step.dict())

	return step


@router.get('/study/{study_id}/step/', response_model=List[StepSchema], tags=[Tags.step])
async def get_all_steps(study_id: int, db: Session = Depends(get_db)):
	steps = get_study_steps(db, study_id)

	return steps


@router.get('/study/{study_id}/step/{step_id}', response_model=StepSchema, tags=[Tags.step])
async def get_step(study_id: int, step_id: int, db: Session = Depends(get_db)):
	step = get_step_by_id(db, study_id, step_id)

	return step


@router.get('/study/{study_id}/step/first/', response_model=StepSchema, tags=[Tags.step])
async def get_first_step(study_id: int, db: Session = Depends(get_db)):
	step = get_first_study_step(db, study_id)

	return step


@router.get('/study/{study_id}/step/{step_id}/next', response_model=StepSchema, tags=[Tags.step])
async def get_next_step(study_id: int, step_id: int, db: Session = Depends(get_db)):
	step = get_next_study_step(db, study_id, step_id)

	return step


@router.put('/study/{study_id}/step/{step_id}', response_model=StepSchema, tags=[Tags.step, Tags.admin])
async def update_step(study_id: int, step_id: int, step: NewStepSchema, db: Session = Depends(get_db),
					current_user: AdminUser = Depends(get_current_active_user)):
	step = update_study_step(db=db, study_id=study_id, step_id=step_id, **step.dict())

	return step
	

@router.delete('/study/{study_id}/step/{step_id}', response_model=StepSchema, tags=[Tags.step, Tags.admin])
async def delete_step(study_id: int, step_id: int, db: Session = Depends(get_db),
					current_user: AdminUser = Depends(get_current_active_user)):
	step = delete_study_step(db, study_id, step_id)

	return step


"""
Page routes
"""
@router.post('/study/{study_id}/step/{step_id}/page/', response_model=PageSchema, tags=[Tags.page, Tags.admin])
async def create_new_page(study_id: int, step_id: int, page: NewPageSchema, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	page = create_study_page(db=db, study_id=study_id,
							 step_id=step_id, **page.dict())

	return page


@router.get('/study/{study_id}/step/{step_id}/page/', response_model=List[PageSchema], tags=[Tags.page])
async def get_all_pages(study_id: int, step_id: int, db: Session = Depends(get_db)):
	pages = get_study_pages(db, study_id, step_id)

	return pages


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}', response_model=PageSchema, tags=[Tags.page])
async def get_page(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db)):
	page = get_page_by_id(db, study_id, step_id, page_id)

	return page


@router.get('/study/{study_id}/step/{step_id}/page/first/', response_model=PageSchema, tags=[Tags.page])
async def get_first_page(study_id: int, step_id: int, db: Session = Depends(get_db)):
	page = get_first_step_page(db, study_id, step_id)

	return page


@router.get('/study/{study_id}/step/{step_id}/page/last/', response_model=PageSchema, tags=[Tags.page])
async def get_last_page(study_id: int, step_id: int, db: Session = Depends(get_db)):
	page = get_last_step_page(db, study_id, step_id)

	return page


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}/next', response_model=PageSchema, tags=[Tags.page])
async def get_next_page(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db)):
	page = get_next_step_page(db, study_id, step_id, page_id)

	return page


@router.put('/study/{study_id}/step/{step_id}/page/{page_id}', response_model=PageSchema, tags=[Tags.page, Tags.admin])
async def update_page(study_id: int, step_id: int, page_id: int, page: NewPageSchema, db: Session = Depends(get_db),
					current_user: AdminUser = Depends(get_current_active_user)):
	page = update_step_page(db=db, study_id=study_id, step_id=step_id, page_id=page_id, **page.dict())

	return page


@router.delete('/study/{study_id}/step/{step_id}/page/{page_id}', response_model=PageSchema, tags=[Tags.page, Tags.admin])
async def delete_page(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db),
					current_user: AdminUser = Depends(get_current_active_user)):
	page = delete_step_page(db, study_id, step_id, page_id)

	return page


"""
Question routes
"""
@router.post('/study/{study_id}/step/{step_id}/page/{page_id}/question/', response_model=QuestionSchema, tags=[Tags.question, Tags.admin])
async def create_new_question(study_id: int, step_id: int, page_id: int, question: NewQuestionSchema, db: Session = Depends(get_db),
							current_user: AdminUser = Depends(get_current_active_user)):
	question = create_survey_question(
		db=db, study_id=study_id, step_id=step_id, page_id=page_id, **question.dict())

	return question


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}/question/', response_model=List[QuestionSchema], tags=[Tags.question])
async def get_questions(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db)):
	questions = get_page_questions(
		db=db, study_id=study_id, step_id=step_id, page_id=page_id)

	return questions


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}/question/{question_id}', response_model=QuestionSchema, tags=[Tags.question])
async def get_question(study_id: int, step_id: int, page_id: int, question_id: int, db: Session = Depends(get_db)):
	question = get_question_by_id(
		db=db, study_id=study_id, step_id=step_id, page_id=page_id, question_id=question_id)

	return question


@router.put('/study/{study_id}/step/{step_id}/page/{page_id}/question/{question_id}', response_model=QuestionSchema, tags=[Tags.question, Tags.admin])
async def update_question(study_id: int, step_id: int, page_id: int, question_id: int, question: NewQuestionSchema, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	question = update_survey_question(
		db=db, study_id=study_id, step_id=step_id, page_id=page_id, question_id=question_id, **question.dict())

	return question


@router.delete('/study/{study_id}/step/{step_id}/page/{page_id}/question/{question_id}', response_model=QuestionSchema, tags=[Tags.question, Tags.admin])
async def delete_question(study_id: int, step_id: int, page_id: int, question_id: int, db: Session = Depends(get_db),
						current_user: AdminUser = Depends(get_current_active_user)):
	question = delete_survey_question(
		db=db, study_id=study_id, step_id=step_id, page_id=page_id, question_id=question_id)

	return question
