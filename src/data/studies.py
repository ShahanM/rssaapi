from sqlalchemy.orm import Session
from .models.study import *
from .models.studyschema import *
import random
from typing import List
from .studydatabase import engine
import json
import os


def create_database():
	Study.__table__.create(bind=engine, checkfirst=True)
	StudyCondition.__table__.create(bind=engine, checkfirst=True)
	Step.__table__.create(bind=engine, checkfirst=True)
	Page.__table__.create(bind=engine, checkfirst=True)
	PageQuestion.__table__.create(bind=engine, checkfirst=True)


"""
Study Queries
"""
def create_study(db: Session, studyname: str) -> Study:
	study = Study(study_name=studyname)
	db.add(study)
	db.commit()
	db.refresh(study)

	return study


def get_studies(db: Session) -> List[Study]:
	studies = db.query(Study).all()
	
	return studies


def get_study_by_id(db: Session, study_id: int) -> Study:
	study = db.query(Study).filter(Study.id == study_id).first()
	if study:
		return study
	else:
		raise Exception("Study not found")


def update_study(db: Session, study_id: int, study_name: str) -> Study:
	study = get_study_by_id(db, study_id)
	setattr(study, 'study_name', study_name)
	db.add(study)
	db.commit()
	db.refresh(study)

	return study


def delete_study_by_id(db: Session, study_id: int) -> Study:
	study = get_study_by_id(db, study_id)
	db.delete(study)
	db.commit()

	return study


"""
Study Condition Queries
"""
def create_study_condition(db: Session, study_id: int, condition_name: str) -> StudyCondition:
	condition = StudyCondition(study_id=study_id, condition_name=condition_name)
	db.add(condition)
	db.commit()
	db.refresh(condition)

	study = get_study_by_id(db, study_id)
	study.conditions.append(condition)
	db.commit()
	db.refresh(study)

	return condition

def get_study_conditions(db: Session, study_id: int) -> List[StudyCondition]:
	conditions = db.query(StudyCondition).filter(StudyCondition.study_id == study_id).all()
	
	return conditions


def get_study_condition_by_id(db: Session, study_id: int, condition_id: int) -> StudyCondition:
	condition = db.query(StudyCondition).filter(StudyCondition.study_id == study_id).filter(StudyCondition.id == condition_id).first()

	if condition:
		return condition
	else:
		raise Exception("Condition not found")


def is_condition_limit_defined():
	print("Checking if condition limits are defined at ", os.path.abspath('config/conditionlimits.json'))
	return os.path.isfile('config/conditionlimits.json')


def get_random_study_condition_from_bucket(db: Session, study_id: int) -> StudyConditionSchema:
	with open('config/conditionlimits.json') as f:
		condition_limits = json.load(f)
		print("Found condition limits:\n", condition_limits)

	conditions = get_study_conditions(db, study_id)
	condition = random.choice(conditions)

	conditionlimits_key = str(condition.id)
	if condition_limits[conditionlimits_key] > 0:
		condition_limits[conditionlimits_key] -= 1

		print("New condition limits:\n", condition_limits)
		with open('config/conditionlimits.json', 'w') as f:
			json.dump(condition_limits, f)
		return condition
	else:
		return get_random_study_condition_from_bucket(db, study_id)


def get_random_study_condition(db: Session, study_id: int) -> StudyConditionSchema:
	if is_condition_limit_defined():
		print("Using condition limits")
		return get_random_study_condition_from_bucket(db, study_id)
	print("Not using condition limits")
	conditions = get_study_conditions(db, study_id)
	condition = random.choice(conditions)

	return condition


def update_study_condition(db: Session, study_id: int, condition_id: int, condition_name: str) -> StudyCondition:
	condition = get_study_condition_by_id(db, study_id, condition_id)
	setattr(condition, 'condition_name', condition_name)
	db.add(condition)
	db.commit()
	db.refresh(condition)

	return condition


def delete_study_condition(db: Session, study_id: int, condition_id: int) -> StudyCondition:
	condition = get_study_condition_by_id(db, study_id, condition_id)
	db.delete(condition)
	db.commit()

	return condition


"""
Step Queries
"""
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
		raise Exception("Step not found")


def get_first_study_step(db: Session, study_id: int) -> Step:
	step = db.query(Step).filter(Step.study_id == study_id).order_by(Step.step_order).first()

	if step:
		return step
	else:
		raise Exception("There are no steps defined for this study.")

def get_next_study_step(db: Session, study_id: int, step_id: int) -> Step:
	current = get_step_by_id(db, study_id, step_id)
	step = db.query(Step).filter(Step.study_id == study_id).filter(Step.step_order > current.step_order).order_by(Step.step_order).first()

	if step:
		return step
	else:
		return Step()


def update_study_step(db: Session, study_id: int, step_id: int, step_order: int, \
	step_name: str, step_description: str) -> Step:
	step = get_step_by_id(db, study_id, step_id)
	setattr(step, 'step_order', step_order)
	setattr(step, 'step_name', step_name)
	setattr(step, 'step_description', step_description)
	db.add(step)
	db.commit()
	db.refresh(step)

	return step


def delete_study_step(db: Session, study_id: int, step_id: int) -> Step:
	step = get_step_by_id(db, study_id, step_id)
	db.delete(step)
	db.commit()

	return step


"""
Page Queries
"""
def create_study_page(db: Session, study_id: int, step_id: int, \
	page_order: int, page_name: str, page_instruction: str) -> Page:

	# FIXME page_order should be unique for a step
	page = Page(study_id=study_id, step_id=step_id, page_order=page_order, \
		page_name=page_name, page_instruction=page_instruction)
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
		raise Exception("Page not found")


def get_first_step_page(db: Session, study_id: int, step_id: int) -> Page:
	page = db.query(Page).filter(Page.study_id == study_id).filter(Page.step_id == step_id).order_by(Page.page_order).first()

	if page:
		return page
	else:
		raise Exception("There are no pages defined for this step.")


def get_last_step_page(db: Session, study_id: int, step_id: int) -> Page:
	page = db.query(Page).filter(Page.study_id == study_id).filter(Page.step_id == step_id).order_by(Page.page_order.desc()).first()

	if page:
		return page
	else:
		raise Exception("There are no pages defined for this step.")


def get_next_step_page(db: Session, study_id: int, step_id: int, page_id: int) -> Page:
	current = get_page_by_id(db, study_id, step_id, page_id)
	page = db.query(Page).filter(Page.study_id == study_id).filter(Page.step_id == step_id).filter(Page.page_order > current.page_order).order_by(Page.page_order).first()

	if page:
		return page
	else:
		return Page()


def update_step_page(db: Session, study_id: int, step_id: int, page_id: int, \
	page_order: int, page_name: str, page_instruction: str) -> Page:
	page = get_page_by_id(db, study_id, step_id, page_id)
	setattr(page, 'page_order', page_order)
	setattr(page, 'page_name', page_name)
	setattr(page, 'page_instruction', page_instruction)
	db.add(page)
	db.commit()
	db.refresh(page)

	return page


def delete_step_page(db: Session, study_id: int, step_id: int, page_id: int) -> Page:
	page = get_page_by_id(db, study_id, step_id, page_id)
	db.delete(page)
	db.commit

	return page


"""
Question Queries
"""
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


def get_question_by_id(db: Session, study_id: int, step_id: int, page_id: int, question_id: int) -> PageQuestion:
	question = db.query(PageQuestion).filter(PageQuestion.study_id == study_id).filter(PageQuestion.step_id == step_id).filter(PageQuestion.page_id == page_id).filter(PageQuestion.id == question_id).first()

	if question:
		return question
	else:
		raise Exception("Question not found")


def get_all_survey_questions(db: Session, study_id: int) -> List[PageQuestion]:
	questions = db.query(PageQuestion).filter(PageQuestion.study_id == study_id).all()
	
	return questions


def get_count_of_questions_by_study_id(db: Session, study_id: int) -> int:
	count = db.query(PageQuestion).filter(PageQuestion.study_id == study_id).count()
	
	return count


def update_survey_question(db: Session, study_id: int, step_id: int, page_id: int, question_id: int, \
	question_order: int, questiontxt: str) -> PageQuestion:
	question = get_question_by_id(db, study_id, step_id, page_id, question_id)
	setattr(question, 'question_order', question_order)
	# setattr(question, 'page_id', 'page_id')
	setattr(question, 'question', questiontxt)
	db.add(question)
	db.commit()
	db.refresh(question)

	return question


def delete_survey_question(db: Session, study_id: int, step_id: int, page_id: int, question_id: int) -> PageQuestion:
	question = db.query(PageQuestion).filter(PageQuestion.study_id == study_id).filter(PageQuestion.step_id == step_id).filter(PageQuestion.page_id == page_id).filter(PageQuestion.id == question_id).first()
	db.delete(question)
	db.commit()

	if question:
		return question
	else:
		return PageQuestion()
