from datetime import datetime
from enum import unique
from dataclasses import dataclass
from typing import List
from data.userdatabase import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class User(Base):
	__tablename__ = 'user'
	salt = 144

	id = Column(Integer, primary_key=True, autoincrement=True)
	date_created = Column(DateTime, nullable=False, default=datetime.utcnow)

	condition = Column(Integer, nullable=False)

	user_type_id = Column(Integer, ForeignKey('user_type.id'), nullable=False)
	user_type = relationship('UserType', back_populates='users')
	
	seen_items = relationship('SeenItem', back_populates='user', \
		uselist=True, cascade='all, delete-orphan')


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
	item_id = Column(Integer, nullable=False)
	page_id = Column(Integer, nullable=False)

	user = relationship('User', back_populates='seen_items', \
		uselist=True)

	page_level = Column(Integer, nullable=False)




# user_response = db.Table('user_response',
# 	db.Column('response_id', db.Integer, db.ForeignKey('survey_response.id'), \
# 		primary_key=True),
# 	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
# )


# user_condition = db.Table('user_condition',
# 	db.Column('condition_id', db.Integer, db.ForeignKey('study_condition.id'), \
# 		primary_key=True),
# 	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
# )

# class Condition(db.Model):
# 	__tablename__ = 'study_condition'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id:int = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	cond_tag = db.Column(db.String(144), nullable=False)
# 	cond_act = db.Column(db.String(144), nullable=False)
# 	cond_exp = db.Column(db.Text, nullable=True)

# 	participants = db.relationship('User', secondary=user_condition, \
# 		lazy='subquery', backref=db.backref('user'))




# class SurveyPage(db.Model):
# 	__tablename__ = 'survey_page'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	page_num = db.Column(db.Integer, nullable=False)

# 	page_title = db.Column(db.String(144), nullable=False)
# 	page_type = db.Column(db.String(36), nullable=False)

# 	seen_items = db.relationship('SeenItem', backref='seen_items', \
# 		lazy=True)
# 	questions = db.relationship('SurveyQuestion', backref='survey_question', \
# 		lazy=True)
# 	reponses = db.relationship('SurveyResponse', backref='survey_response', \
# 		lazy=True)

# 	interactions = db.relationship('UserInteraction', \
# 		backref='user_interaction', lazy=True)

# 	def __repr__(self) -> str:
# 		return '<Survey %r>' % self.id

	
# class SurveyQuestion(db.Model):
# 	__tablename__ = 'survey_question'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	question_type = db.Column(db.String(36), nullable=False)
# 	question_text = db.Column(db.String(144), nullable=False)
# 	question_tag = db.Column(db.String(144), nullable=True)

# 	responses = db.relationship('FreeResponse', backref='question_response', \
# 		lazy=True)
# 	scores = db.relationship('Score', backref='likert_score', \
# 		lazy=True)
	
# 	survey_page = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
# 		nullable=False)


# @dataclass
# class SurveyResponse(db.Model):
# 	__tablename__ = 'survey_response'

# 	id:int = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	starttime:datetime = db.Column(db.DateTime, nullable=False)
# 	endtime:datetime = db.Column(db.DateTime, nullable=False)

# 	responses:list = db.relationship('FreeResponse', backref='free_response')
# 	scores:list = db.relationship('Score', backref='score')
# 	ratings:list = db.relationship('Rating', backref='movie_rating', \
# 		lazy=True)

# 	user:int = db.Column(db.Integer, db.ForeignKey('user.id'), \
# 		nullable=False)
# 	survey_page:int = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
# 		nullable=False)


# @dataclass
# class FreeResponse(db.Model):
# 	__tablename__ = 'free_response'
	
# 	id:int = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id:int = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	user_id:int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	response_text:str = db.Column(db.Text)

# 	question:int = db.Column(db.Integer, db.ForeignKey('survey_question.id'), \
# 		nullable=False)
# 	survey_response:int = db.Column(db.Integer, db.ForeignKey('survey_response.id'), \
# 		nullable=False)


# @dataclass
# class Score(db.Model):
# 	__tablename__ = 'score'

# 	id:int = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	user_id:int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	score_point:int = db.Column(db.Integer)

# 	question:int = db.Column(db.Integer, db.ForeignKey('survey_question.id'), \
# 		nullable=False)
# 	survey_response:int = db.Column(db.Integer, db.ForeignKey('survey_response.id'), \
# 		nullable=False)


# @dataclass
# class Rating(db.Model):
# 	__tablename__ = 'rating'

# 	id:int = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	user_id:int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	date_created:datetime = db.Column(db.DateTime, nullable=False)
# 	item_id:int = db.Column(db.Integer, nullable=False)
# 	rating:int = db.Column(db.Integer, nullable=False)

# 	location:str = db.Column(db.String(45), nullable=False)
# 	level:int = db.Column(db.Integer, nullable=False)

# 	survey_response:int = db.Column(db.Integer, db.ForeignKey('survey_response.id'), \
# 		nullable=False)


# class UserInteraction(db.Model):
# 	__tablename__ = 'user_interaction'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	page_id = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
# 		nullable=False)
# 	action_type = db.Column(db.String(144), nullable=False)
	
# 	action_target = db.Column(db.Integer, db.ForeignKey('action_target.id'), \
# 		nullable=False)
# 	timestamp = db.Column(db.DateTime, nullable=False)


# class ActionTarget(db.Model):
# 	__tablename__ = 'action_target'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	target_label = db.Column(db.String(144), nullable=False)
# 	target_type = db.Column(db.String(144))


# class HoverHistory(db.Model):
# 	__tablename__ = 'hover_history'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	page_id = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
# 		nullable=False)

# 	item_id = db.Column(db.Integer, nullable=False)
# 	level = db.Column(db.Integer, nullable=False)

# 	location = db.Column(db.String(144))

# 	timestamp = db.Column(db.DateTime, nullable=False)
# 	event_type = db.Column(db.String(81), nullable=False)


# class RatingHistory(db.Model):
# 	__tablelname__ = 'rating_history'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)	
# 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	
# 	page_id = db.Column(db.Integer, db.ForeignKey('survey_page.id'), \
# 		nullable=False)

# 	item_id = db.Column(db.Integer, nullable=False)
# 	level = db.Column(db.Integer, nullable=False)

# 	location = db.Column(db.String(144))

# 	timestamp = db.Column(db.DateTime, nullable=False)
# 	rating = db.Column(db.Integer, nullable=False)


# class Demography(db.Model):
# 	__tablename__ = 'demography'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	age = db.Column(db.Integer, nullable=False)
# 	race = db.Column(db.String(144), nullable=False)
# 	gender = db.Column(db.Integer, nullable=False)
# 	country = db.Column(db.String(81), nullable=False)
# 	education = db.Column(db.Integer, nullable=False)


# class RequestLog(db.Model):
# 	__tablename__ = 'request_log'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	timestamp = db.Column(db.DateTime, nullable=False)
# 	rawheader = db.Column(db.Text, nullable=False)
# 	useragent = db.Column(db.Text, nullable=False)
# 	origin = db.Column(db.String(144), nullable=False)
# 	referer = db.Column(db.String(144), nullable=False)

# 	endpoint = db.Column(db.String(144), nullable=False)



# class PlatformSession(db.Model):
# 	__tablename__ = 'platform_session'

# 	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
# 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
# 	date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# 	timestamp = db.Column(db.DateTime, nullable=False)
# 	platform_type = db.Column(db.String(144), nullable=False)
# 	platform_id = db.Column(db.String(144), nullable=False)
# 	study_id = db.Column(db.String(144), nullable=False)
# 	session_id = db.Column(db.String(144), nullable=False)
