from datetime import datetime
from enum import unique
from dataclasses import dataclass
from typing import List
# from data.userdatabase import Base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'
	salt = 144

	id = Column(Integer, primary_key=True, autoincrement=True)
	date_created = Column(DateTime, nullable=False, default=datetime.utcnow)

	study_id = Column(Integer, nullable=False)
	condition = Column(Integer, nullable=False)

	user_type_id = Column(Integer, ForeignKey('user_type.id'), nullable=False)
	user_type = relationship('UserType', back_populates='users')
	
	seen_items = relationship('SeenItem', back_populates='user', \
		uselist=True, cascade='all, delete-orphan')
	
	responses = relationship('SurveyResponse', back_populates='user', \
		uselist=True, cascade='all, delete-orphan')
	text_responses = relationship('SurveyTextResponse', back_populates='user', \
		uselist=True, cascade='all, delete-orphan')

	rated_items = relationship('RatingResponse', back_populates='user', \
		uselist=True, cascade='all, delete-orphan', overlaps='rated_items')

	emotion_preference = relationship('EmotionPreference', \
		back_populates='user', uselist=False, cascade='all, delete-orphan')
	
	interaction_log = relationship('InteractionLog', back_populates='user', \
		uselist=False, cascade='all, delete-orphan')
	
	demographic_info = relationship('DemographicInfo', back_populates='user', \
		uselist=False, cascade='all, delete-orphan')

	# selected_item = Column(Integer, nullable=True)


class UserType(Base):
	__tablename__ = 'user_type'

	id = Column(Integer, primary_key=True, autoincrement=True)

	type_str = Column(String(144), nullable=False)

	users = relationship('User', back_populates='user_type', \
		uselist=True, cascade='all, delete-orphan')
		

class SeenItem(Base):
	__tablename__ = 'seen_item'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	page_id = Column(Integer, nullable=False)
	item_id = Column(Integer, nullable=False)

	user = relationship('User', back_populates='seen_items', \
		uselist=True)

	page_level = Column(Integer, nullable=False)


class SurveyResponse(Base):
	__tablename__ = 'survey_response'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	study_id = Column(Integer, nullable=False)
	page_id = Column(Integer, nullable=False)
	question_id = Column(Integer, nullable=False)

	# response value for closed-ended questions, mostly Likert scale
	response = Column(Integer, nullable=False)

	user = relationship('User', back_populates='responses')


class SurveyTextResponse(Base):
	__tablename__ = 'survey_text_response'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	study_id = Column(Integer, nullable=False)
	page_id = Column(Integer, nullable=False)
	question_id = Column(Integer, nullable=False)

	response = Column(String(144), nullable=False)

	user = relationship('User', back_populates='text_responses')


class RatingResponse(Base):
	__tablename__ = 'rating_response'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	study_id = Column(Integer, nullable=False)
	page_id = Column(Integer, nullable=False)
	item_id = Column(Integer, nullable=False)

	rating = Column(Integer, nullable=False)

	user = relationship('User', back_populates='rated_items')

	page_level = Column(Integer, nullable=False)


class EmotionPreference(Base):
	__tablename__ = 'emotion_preference'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

	anger = Column(Numeric, nullable=False, default=-1.0)
	anticipation = Column(Numeric, nullable=False, default=-1.0)
	disgust = Column(Numeric, nullable=False, default=-1.0)
	fear = Column(Numeric, nullable=False, default=-1.0)
	joy = Column(Numeric, nullable=False, default=-1.0)
	surprise = Column(Numeric, nullable=False, default=-1.0)
	sadness = Column(Numeric, nullable=False, default=-1.0)
	trust = Column(Numeric, nullable=False, default=-1.0)

	user = relationship('User', back_populates='emotion_preference')

class InteractionLog(Base):
	__tablename__ = 'interaction_log'

	id = Column(Integer, primary_key=True, autoincrement=True)
	
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	study_id = Column(Integer, nullable=False)
	step_id = Column(Integer, nullable=False)
	
	# steps with one page only has no page_id
	page_id = Column(Integer, nullable=True)

	user = relationship('User', back_populates='interaction_log')

	# time of interaction (UTC) logged
	time = Column(DateTime, nullable=False, default=datetime.utcnow)
	time_spent = Column(Integer, nullable=False)

	# action_type: 'click', 'rating', 'text', 'next', 'back'
	interaction_type = Column(String(144), nullable=False)
	# for the gallery, the target is in the form of 'gallery:pagenum'
	interaction_target = Column(String(144), nullable=False)

	# only applicable for rating action
	item_id = Column(Integer, nullable=True)
	rating = Column(Integer, nullable=True)


class DemographicInfo(Base):
	__tablename__ = 'demographic_info'

	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
	study_id = Column(Integer, nullable=False)

	age = Column(Integer, nullable=False)
	gender = Column(String(144), nullable=False)
	education = Column(String(144), nullable=False)

	user = relationship('User', back_populates='demographic_info')
