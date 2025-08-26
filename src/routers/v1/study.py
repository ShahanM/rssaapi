from datetime import datetime
from typing import Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.studies import *
from data.studydatabase import SessionLocal
from docs.metadata import TagsMetadataEnum as Tags

from .admin import AdminUser, get_current_active_user

router = APIRouter(prefix='/v1')

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

class QuestionSchema(BaseModel):
	id: Union[int, None]
	page_id: Union[int, None]
	question_order: Union[int, None]
	question: Union[str, None]

	class Config:
		orm_mode = True


class NewQuestionSchema(BaseModel):
	question_order: int
	questiontxt: str


class PageSchema(BaseModel):
	id: Union[int, None]
	step_id: Union[int, None]
	page_order: Union[int, None]
	page_name: Union[str, None]
	page_instruction: Union[str, None]

	questions: List[QuestionSchema]

	class Config:
		orm_mode = True


class NewPageSchema(BaseModel):
	page_order: int
	page_name: str
	page_instruction: str


class StepSchema(BaseModel):
	id: Union[int, None]
	study_id: Union[int, None]
	step_order: Union[int, None]
	step_name: Union[str, None]
	step_description: Union[str, None]

	# pages: List[PageSchema]

	class Config:
		orm_mode = True


class NewStepSchema(BaseModel):
	step_order: int
	step_name: str
	step_description: str


class StudyConditionSchema(BaseModel):
	id: int
	study_id: int
	condition_name: str

	class Config:
		orm_mode = True


class StudySchema(BaseModel):
	id: int
	date_created: datetime
	study_name: str

	# steps: List[StepSchema]
	conditions: List[StudyConditionSchema]

	class Config:
		orm_mode = True


class NewConditionSchema(BaseModel):
	condition_name: str


"""
Study routes
"""
@router.post('/study/create_db/', tags=[Tags.meta])
async def create_db(db: Session = Depends(get_db),
                    current_user: AdminUser = Depends(get_current_active_user)):
    create_database()

    return "Database created"


@router.post('/study/', response_model=StudySchema, tags=[Tags.study])
async def create_new_study(studyname: str, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    study = create_study(db=db, studyname=studyname)

    return study


@router.get('/study/', response_model=List[StudySchema], tags=[Tags.study])
async def get_all_studies(db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    studies = get_studies(db)

    return studies


@router.get('/study/{study_id}', response_model=StudySchema, tags=[Tags.study])
async def get_study(study_id: int, db: Session = Depends(get_db)):
    study = get_study_by_id(db, study_id)

    return study


@router.put('/study/{study_id}', response_model=StudySchema, tags=[Tags.study])
async def update_study_details(study_id: int, study_name: str, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    study = update_study(db=db, study_id=study_id, study_name=study_name)

    return study


@router.delete('/study/{study_id}', response_model=StudySchema, tags=[Tags.study])
async def delete_study(study_id: int, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    study = delete_study_by_id(db, study_id)

    return study


"""
Condition routes
"""
@router.post('/study/{study_id}/condition/', response_model=StudyConditionSchema, tags=[Tags.meta])
async def create_new_condition(study_id: int, condition: NewConditionSchema, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    condition = create_study_condition(db=db, study_id=study_id, **condition.dict())

    return condition


@router.get('/study/{study_id}/condition/', response_model=List[StudyConditionSchema], tags=[Tags.meta])
async def get_all_conditions(study_id: int, db: Session = Depends(get_db)):
    conditions = get_study_conditions(db, study_id)

    return conditions


@router.get('/study/{study_id}/condition/{condition_id}', response_model=StudyConditionSchema, tags=[Tags.meta])
async def get_condition(study_id: int, condition_id: int, db: Session = Depends(get_db)):
    condition = get_study_condition_by_id(db, study_id, condition_id)

    return condition


@router.get('/study/{study_id}/condition/random/', response_model=StudyConditionSchema, tags=[Tags.study])
async def get_random_condition(study_id: int, db: Session = Depends(get_db)):
    condition = get_random_study_condition(db, study_id)

    return condition


@router.put('/study/{study_id}/condition/{condition_id}', response_model=StudyConditionSchema, tags=[Tags.meta])
async def update_condition(study_id: int, condition_id: int, condition: NewConditionSchema, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    condition = update_study_condition(db=db, study_id=study_id, condition_id=condition_id, **condition.dict())

    return condition


@router.delete('/study/{study_id}/condition/{condition_id}', response_model=StudyConditionSchema, tags=[Tags.meta])
async def delete_condition(study_id: int, condition_id: int, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    condition = delete_study_condition(db=db, study_id=study_id, condition_id=condition_id)

    return condition


"""
Step routes
"""
@router.post('/study/{study_id}/step/', response_model=StepSchema, tags=[Tags.meta])
async def create_new_step(study_id: int, step: NewStepSchema, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    step = create_study_step(db=db, study_id=study_id, **step.dict())

    return step


@router.get('/study/{study_id}/step/', response_model=List[StepSchema], tags=[Tags.study])
async def get_all_steps(study_id: int, db: Session = Depends(get_db)):
    steps = get_study_steps(db, study_id)

    return steps


@router.get('/study/{study_id}/step/{step_id}', response_model=StepSchema, tags=[Tags.study])
async def get_step(study_id: int, step_id: int, db: Session = Depends(get_db)):
    step = get_step_by_id(db, study_id, step_id)

    return step


@router.get('/study/{study_id}/step/first/', response_model=StepSchema, tags=[Tags.study])
async def get_first_step(study_id: int, db: Session = Depends(get_db)):
    step = get_first_study_step(db, study_id)

    return step


@router.get('/study/{study_id}/step/{step_id}/next', response_model=StepSchema, tags=[Tags.study])
async def get_next_step(study_id: int, step_id: int, db: Session = Depends(get_db)):
    step = get_next_study_step(db, study_id, step_id)

    return step


@router.put('/study/{study_id}/step/{step_id}', response_model=StepSchema, tags=[Tags.meta])
async def update_step(study_id: int, step_id: int, step: NewStepSchema, db: Session = Depends(get_db),
                    current_user: AdminUser = Depends(get_current_active_user)):
    step = update_study_step(db=db, study_id=study_id, step_id=step_id, **step.dict())

    return step


@router.delete('/study/{study_id}/step/{step_id}', response_model=StepSchema, tags=[Tags.meta])
async def delete_step(study_id: int, step_id: int, db: Session = Depends(get_db),
                    current_user: AdminUser = Depends(get_current_active_user)):
    step = delete_study_step(db, study_id, step_id)

    return step


"""
Page routes
"""
@router.post('/study/{study_id}/step/{step_id}/page/', response_model=PageSchema, tags=[Tags.meta])
async def create_new_page(study_id: int, step_id: int, page: NewPageSchema, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    page = create_study_page(db=db, study_id=study_id, step_id=step_id, **page.dict())

    return page


@router.get('/study/{study_id}/step/{step_id}/page/', response_model=List[PageSchema], tags=[Tags.study])
async def get_all_pages(study_id: int, step_id: int, db: Session = Depends(get_db)):
    pages = get_study_pages(db, study_id, step_id)

    return pages


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}', response_model=PageSchema, tags=[Tags.study])
async def get_page(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db)):
    page = get_page_by_id(db, study_id, step_id, page_id)

    return page


@router.get('/study/{study_id}/step/{step_id}/page/first/', response_model=PageSchema, tags=[Tags.study])
async def get_first_page(study_id: int, step_id: int, db: Session = Depends(get_db)):
    page = get_first_step_page(db, study_id, step_id)

    return page


@router.get('/study/{study_id}/step/{step_id}/page/last/', response_model=PageSchema, tags=[Tags.study])
async def get_last_page(study_id: int, step_id: int, db: Session = Depends(get_db)):
	page = get_last_step_page(db, study_id, step_id)

	return page


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}/next', response_model=PageSchema, tags=[Tags.study])
async def get_next_page(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db)):
    page = get_next_step_page(db, study_id, step_id, page_id)

    return page


@router.put('/study/{study_id}/step/{step_id}/page/{page_id}', response_model=PageSchema, tags=[Tags.meta])
async def update_page(study_id: int, step_id: int, page_id: int, page: NewPageSchema, db: Session = Depends(get_db),
                    current_user: AdminUser = Depends(get_current_active_user)):
    page = update_step_page(db=db, study_id=study_id, step_id=step_id, page_id=page_id, **page.dict())

    return page


@router.delete('/study/{study_id}/step/{step_id}/page/{page_id}', response_model=PageSchema, tags=[Tags.meta])
async def delete_page(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db),
                    current_user: AdminUser = Depends(get_current_active_user)):
    page = delete_step_page(db, study_id, step_id, page_id)

    return page


"""
Question routes
"""
@router.post('/study/{study_id}/step/{step_id}/page/{page_id}/question/', response_model=QuestionSchema, tags=[Tags.meta])
async def create_new_question(study_id: int, step_id: int, page_id: int, question: NewQuestionSchema, db: Session = Depends(get_db),
                            current_user: AdminUser = Depends(get_current_active_user)):
    question = create_survey_question(
        db=db, study_id=study_id, step_id=step_id, page_id=page_id, **question.dict())

    return question


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}/question/', response_model=List[QuestionSchema], tags=[Tags.study])
async def get_questions(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db)):
    questions = get_page_questions(
        db=db, study_id=study_id, step_id=step_id, page_id=page_id)

    return questions


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}/question/{question_id}', response_model=QuestionSchema, tags=[Tags.study])
async def get_question(study_id: int, step_id: int, page_id: int, question_id: int, db: Session = Depends(get_db)):
    question = get_question_by_id(
        db=db, study_id=study_id, step_id=step_id, page_id=page_id, question_id=question_id)

    return question


@router.put('/study/{study_id}/step/{step_id}/page/{page_id}/question/{question_id}', response_model=QuestionSchema, tags=[Tags.meta])
async def update_question(study_id: int, step_id: int, page_id: int, question_id: int, question: NewQuestionSchema, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    question = update_survey_question(
        db=db, study_id=study_id, step_id=step_id, page_id=page_id, question_id=question_id, **question.dict())

    return question


@router.delete('/study/{study_id}/step/{step_id}/page/{page_id}/question/{question_id}', response_model=QuestionSchema, tags=[Tags.meta])
async def delete_question(study_id: int, step_id: int, page_id: int, question_id: int, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    question = delete_survey_question(
        db=db, study_id=study_id, step_id=step_id, page_id=page_id, question_id=question_id)

    return question
