from sqlalchemy.orm import Session
from .models.study import Study, Step, Page, StudyCondition, PageQuestion
from typing import List
from .userdatabase import engine

def get_study_by_id(db: Session, study_id: int) -> Study:
	study = db.query(Study).filter(Study.study_id == study_id).first()
	if study:
		return study
	else:
		return Study()

def create_database():
	Study.__table__.create(bind=engine, checkfirst=True)
	StudyCondition.__table__.create(bind=engine, checkfirst=True)
	Step.__table__.create(bind=engine, checkfirst=True)
	Page.__table__.create(bind=engine, checkfirst=True)
	PageQuestion.__table__.create(bind=engine, checkfirst=True)
