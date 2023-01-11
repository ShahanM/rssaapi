from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.utils import *
from data.studydatabase import SessionLocal
from data.models.studyschema import *
from data.studies import *
from .admin import get_current_active_user, AdminUser
from util.docs_metadata import TagsMetadataEnum as Tags

router = APIRouter()

# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post('/study/create_db/', tags=[Tags.admin])
async def create_db(db: Session = Depends(get_db),
                    current_user: AdminUser = Depends(get_current_active_user)):
    create_database()

    return "Database created"


@router.put('/study/', response_model=StudySchema, tags=[Tags.study, Tags.admin])
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


@router.put('/study/{study_id}/step/', response_model=StepSchema, tags=[Tags.step, Tags.admin])
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


@router.delete('/study/{study_id}/step/{step_id}', response_model=StepSchema, tags=[Tags.step, Tags.admin])
async def delete_step(study_id: int, step_id: int, db: Session = Depends(get_db),
                    current_user: AdminUser = Depends(get_current_active_user)):
    step = delete_study_step(db, study_id, step_id)

    return step


@router.put('/study/{study_id}/step/{step_id}/page/', response_model=PageSchema, tags=[Tags.page, Tags.admin])
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


@router.get('/study/{study_id}/step/{step_id}/page/{page_id}/next', response_model=PageSchema, tags=[Tags.page])
async def get_next_page(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db)):
    page = get_next_step_page(db, study_id, step_id, page_id)

    return page


@router.delete('/study/{study_id}/step/{step_id}/page/{page_id}', response_model=PageSchema, tags=[Tags.page, Tags.admin])
async def delete_page(study_id: int, step_id: int, page_id: int, db: Session = Depends(get_db),
                    current_user: AdminUser = Depends(get_current_active_user)):
    page = delete_study_page(db, study_id, step_id, page_id)

    return page


@router.put('/study/{study_id}/step/{step_id}/page/{page_id}/question/', response_model=QuestionSchema, tags=[Tags.question, Tags.admin])
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


@router.delete('/study/{study_id}/step/{step_id}/page/{page_id}/question/{question_id}', response_model=QuestionSchema, tags=[Tags.question, Tags.admin])
async def delete_question(study_id: int, step_id: int, page_id: int, question_id: int, db: Session = Depends(get_db),
                        current_user: AdminUser = Depends(get_current_active_user)):
    question = delete_survey_question(
        db=db, study_id=study_id, step_id=step_id, page_id=page_id, question_id=question_id)

    return question
