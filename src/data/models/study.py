from datetime import datetime
from enum import unique
from dataclasses import dataclass
from typing import List
from data.userdatabase import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class Study(Base):
	__tablename__ = 'study'
	salt = 144

	id = Column(Integer, primary_key=True, autoincrement=True)
	date_created = Column(DateTime, nullable=False, default=datetime.utcnow)

	study_name = Column(String, nullable=False)

	steps = relationship('Step', back_populates='study', \
		uselist=True, cascade='all, delete-orphan')
	conditions = relationship('StudyCondition', back_populates='study', \
		uselist=True, cascade='all, delete-orphan')


class StudyCondition(Base):
	__tablename__ = 'study_condition'

	id = Column(Integer, primary_key=True, autoincrement=True)
	study_id = Column(Integer, ForeignKey('study.id'), nullable=False)

	condition_name = Column(String, nullable=False)

	study = relationship('Study', back_populates='conditions')


class Step(Base):
	__tablename__ = 'study_step'

	id = Column(Integer, primary_key=True, autoincrement=True)
	study_id = Column(Integer, ForeignKey('study.id'), nullable=False)
	
	step_order = Column(Integer, nullable=False)
	step_name = Column(String, nullable=False)
	step_description = Column(String, nullable=True)

	study = relationship('Study', back_populates='steps')
	pages = relationship('Page', back_populates='step', \
		uselist=True, cascade='all, delete-orphan')


class Page(Base):
	__tablename__ = 'step_page'

	id = Column(Integer, primary_key=True, autoincrement=True)
	study_id = Column(Integer, ForeignKey('study.id'), nullable=False)
	step_id = Column(Integer, ForeignKey('study_step.id'), nullable=False)

	page_order = Column(Integer, nullable=False)
	page_name = Column(String, nullable=False)

	step = relationship('Step', back_populates='pages')
	questions = relationship('PageQuestion', back_populates='page', \
		uselist=True, cascade='all, delete-orphan')


class PageQuestion(Base):
	__tablename__ = 'page_question'

	id = Column(Integer, primary_key=True, autoincrement=True)
	study_id = Column(Integer, ForeignKey('study.id'), nullable=False)
	step_id = Column(Integer, ForeignKey('study_step.id'), nullable=False)
	page_id = Column(Integer, ForeignKey('step_page.id'), nullable=False)

	question_order = Column(Integer, nullable=False)
	question = Column(String, nullable=False)

	page = relationship('Page', back_populates='questions')
	