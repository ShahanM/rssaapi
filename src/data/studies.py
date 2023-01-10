from sqlalchemy.orm import Session
from .models.study import Study, Step, Page, StudyCondition, PageQuestion
from typing import List
from .studydatabase import engine


def get_study_by_id(db: Session, study_id: int) -> Study:
	study = db.query(Study).filter(Study.id == study_id).first()
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


def create_study(db: Session, studyname: str) -> Study:
	study = Study(study_name=studyname)
	db.add(study)
	db.commit()
	db.refresh(study)

	return study


def get_studies(db: Session) -> List[Study]:
	studies = db.query(Study).all()
	
	return studies


def create_study_step(db: Session, study_id: int, step_order: int, \
	step_name: str, step_description: str) -> Step:

	# FIXME step_order should be unique for a study
	step = Step(study_id=study_id, step_order=step_order, step_name=step_name, \
		step_description=step_description)
	db.add(step)
	db.commit()
	db.refresh(step)

	study = get_study_by_id(db, study_id)
	study.steps.append(step)
	db.commit()
	db.refresh(study)

	return step


def get_study_steps(db: Session, study_id: int) -> List[Step]:
	steps = db.query(Step).filter(Step.study_id == study_id).all()
	
	return steps


def get_step_by_id(db: Session, study_id: int, step_id: int) -> Step:
	step = db.query(Step).filter(Step.study_id == study_id).filter(Step.id == step_id).first()

	if step:
		return step
	else:
		return Step()


def get_first_study_step(db: Session, study_id: int) -> Step:
	step = db.query(Step).filter(Step.study_id == study_id).order_by(Step.step_order).first()

	if step:
		return step
	else:
		return Step()


def get_next_study_step(db: Session, study_id: int, step_id: int) -> Step:
	current = get_step_by_id(db, study_id, step_id)
	step = db.query(Step).filter(Step.study_id == study_id).filter(Step.step_order > current.step_order).order_by(Step.step_order).first()

	if step:
		return step
	else:
		return Step()


def delete_study_step(db: Session, study_id: int, step_id: int) -> Step:
	step = get_step_by_id(db, study_id, step_id)
	db.delete(step)
	db.commit()

	return step


def create_study_page(db: Session, study_id: int, step_id: int, \
	page_order: int, page_name: str) -> Page:

	# FIXME page_order should be unique for a step
	page = Page(study_id=study_id, step_id=step_id, page_order=page_order, \
		page_name=page_name)
	db.add(page)
	db.commit()
	db.refresh(page)

	step = get_step_by_id(db, study_id, step_id)
	step.pages.append(page)
	
	db.commit()
	db.refresh(step)

	return page

#FIXME study pages are not the same as step pages
def get_study_pages(db: Session, study_id: int, step_id: int) -> List[Page]:
	pages = db.query(Page).filter(Page.study_id == study_id).filter(Page.step_id == step_id).all()
	
	return pages


def get_page_by_id(db: Session, study_id: int, step_id: int, page_id: int) -> Page:
	page = db.query(Page).filter(Page.study_id == study_id).filter(Page.step_id == step_id).filter(Page.id == page_id).first()

	if page:
		return page
	else:
		return Page()


def get_first_step_page(db: Session, study_id: int, step_id: int) -> Page:
	page = db.query(Page).filter(Page.study_id == study_id).filter(Page.step_id == step_id).order_by(Page.page_order).first()

	if page:
		return page
	else:
		return Page()


def get_next_step_page(db: Session, study_id: int, step_id: int, page_id: int) -> Page:
	current = get_page_by_id(db, study_id, step_id, page_id)
	page = db.query(Page).filter(Page.study_id == study_id).filter(Page.step_id == step_id).filter(Page.page_order > current.page_order).order_by(Page.page_order).first()

	if page:
		return page
	else:
		return Page()


def delete_study_page(db: Session, study_id: int, step_id: int, page_id: int) -> Page:
	page = get_page_by_id(db, study_id, step_id, page_id)
	db.delete(page)
	db.commit

	return page


def create_survey_question(db: Session, study_id: int, step_id: int, \
	page_id: int, question_order: int, questiontxt: str) -> PageQuestion:
	question = PageQuestion(study_id=study_id, step_id=step_id, page_id=page_id, \
		question_order=question_order, question=questiontxt)
	db.add(question)
	db.commit()
	db.refresh(question)

	page = get_page_by_id(db, study_id, step_id, page_id)
	page.questions.append(question)

	return question


def get_page_questions(db: Session, study_id: int, step_id: int, page_id: int) -> List[PageQuestion]:
	questions = db.query(PageQuestion).filter(PageQuestion.study_id == study_id).filter(PageQuestion.step_id == step_id).filter(PageQuestion.page_id == page_id).all()
	print(questions)
	return questions


def delete_survey_question(db: Session, study_id: int, step_id: int, page_id: int, question_id: int) -> PageQuestion:
	question = db.query(PageQuestion).filter(PageQuestion.study_id == study_id).filter(PageQuestion.step_id == step_id).filter(PageQuestion.page_id == page_id).filter(PageQuestion.id == question_id).first()
	db.delete(question)
	db.commit()

	if question:
		return question
	else:
		return PageQuestion()
