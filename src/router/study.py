from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.utils import *
from data.studydatabase import SessionLocal
from data.models.studyschema import StudySchema, StepSchema
from data.studies import get_study_by_id, create_database

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# @router.get('/study/create_db/')
# async def create_db(db: Session = Depends(get_db)):
# 	create_database()
# 	return "Database created"

@router.get('/study/{id}', response_model=StudySchema, tags=['study'])
async def get_study(study_id: int, db: Session = Depends(get_db)):
	study = get_study_by_id(db, study_id)
	return study

