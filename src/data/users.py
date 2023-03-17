import random
from typing import List

from sqlalchemy.orm import Session

from data.models.schema import EmotionDiscreteInputSchema, RatedItemSchema

from .models.schema import RatedItemSchema
from .models.user import *
from .models.userschema import *
from .userdatabase import engine


def create_user(db: Session, newuser: NewUserSchema) -> User:
	usertype = get_user_type_by_str(db, newuser.user_type)
	user = User(study_id=newuser.study_id, condition=random.choice(newuser.study_conditions), \
		user_type=usertype)

	db.add(user)
	db.commit()
	db.refresh(user)

	return user


def get_user(db: Session, user_id: int) -> User:
	user = db.query(User).filter(User.id == user_id).first()
	if user:
		return user
	else:
		return User()


def get_user_type_by_str(db: Session, type_str: str) -> UserType:
	usertype = db.query(UserType).filter(UserType.type_str == type_str).first()

	if usertype:
		return usertype
	else:
		return UserType(type_str=type_str)


def instantiate_user_response(user: User, study_id: int, \
	page_id: int, questionresponse: NewQuestionResponseSchema) \
		-> SurveyResponse:
	response = SurveyResponse(user=user, study_id=study_id, \
		page_id=page_id, question_id=questionresponse.question_id, \
		response=questionresponse.response)

	return response


def instantiate_user_text_response(user: User, study_id: int, \
	page_id: int, questionresponse: NewQuestionResponseSchema) \
		-> SurveyTextResponse:
	response = SurveyTextResponse(user=user, study_id=study_id, \
		page_id=page_id, question_id=questionresponse.question_id, \
		response=questionresponse.response)

	return response


def create_survey_response(db: Session, user_id: int, \
	newresponse: NewSurveyResponseSchema) -> List[SurveyResponse]:
	user = get_user(db, user_id)

	responses = []

	for qresponse in newresponse.responses:
		responses.append(instantiate_user_response(user, newresponse.study_id, \
			newresponse.page_id, qresponse))

	db.add_all(responses)
	db.commit()

	user.responses.extend(responses)
	db.commit()
	db.refresh(user)

	return responses


def create_survey_text_response(db: Session, user_id: int, \
	newresponse: NewSurveyResponseSchema) -> List[SurveyTextResponse]:
	user = get_user(db, user_id)

	responses = []

	for qresponse in newresponse.responses:
		response = instantiate_user_text_response(user, newresponse.study_id, \
			newresponse.page_id, qresponse)
		responses.append(response)

	db.add_all(responses)
	db.commit()

	user.text_responses.extend(responses)
	db.commit()
	db.refresh(user)

	return responses

def create_rating_response(db: Session, user_id: int, \
	ratings: RatingResponseSchema) -> List[RatingResponse]:
	user = get_user(db, user_id)

	ratingresponses = []

	for rating in ratings.ratings:
		ratingresponses.append(RatingResponse(user=user, \
		page_id=ratings.page_id, item_id=rating.item_id, rating=rating.rating, \
		page_level=ratings.page_level))

	db.add_all(ratingresponses)
	db.commit()

	user.rated_items.extend(ratingresponses)
	db.commit()
	db.refresh(user)

	return ratingresponses


def create_seen_items_if_not_exist(db: Session, user_id: int, \
	seenitems: SeenItemsSchema) -> List[SeenItem]:
	# user = get_user(db, user_id)

	existitems = []
	items = []
	for item in seenitems.items:
		existitem = db.query(SeenItem).filter(SeenItem.user_id == user_id)\
			.filter(SeenItem.page_id == seenitems.page_id)\
			.filter(SeenItem.item_id == item).first()
		if existitem:
			existitems.append(existitem)
			continue
		seenitem = SeenItem(user_id=user_id, page_id=seenitems.page_id, \
			page_level=seenitems.page_level, item_id=item)
		items.append(seenitem)

	db.add_all(items)
	db.commit()
	
	return items + existitems

def create_emotion_preference(db: Session, user_id: int, \
	emotionpref: List[EmotionDiscreteInputSchema]) -> EmotionPreferenceSchema:
	user = get_user(db, user_id)

	emotion_tags = ['anger', 'anticipation', 'disgust', 'fear', \
		'joy', 'sadness', 'surprise', 'trust']
	emo_dict = {emo.emotion.lower(): emo.weight for emo in emotionpref}
	emo_data = {}

	for tag in emotion_tags:
		if emo_dict[tag] == 'low':
			emo_data[tag] = 0.3
		elif emo_dict[tag] == 'high':
			emo_data[tag] = 0.8
		else:
			emo_data[tag] = -1.0

	emotionpref = EmotionPreference(user=user, **emo_data)

	db.add(emotionpref)
	db.commit()

	user.emotion_preference = emotionpref
	db.commit()
	db.refresh(user)

	return emotionpref


def create_item_selection(db: Session, user_id: int, \
	itemselection: SelectionResponseSchema) -> RatingResponse:
	user = get_user(db, user_id)

	selected = RatingResponse(user=user, page_id=itemselection.page_id, \
		item_id=itemselection.selected_item.item_id, rating=99, page_level=0)

	db.add(selected)
	db.commit()
	db.refresh(selected)

	# user.selected_item = itemselection.selected_item.item_id
	user.rated_items.append(selected)
	db.commit()
	db.refresh(user)

	return selected


def create_database(base):
	UserType.__table__.create(bind=engine, checkfirst=True)
	User.__table__.create(bind=engine, checkfirst=True)
	SeenItem.__table__.create(bind=engine, checkfirst=True)
	SurveyResponse.__table__.create(bind=engine, checkfirst=True)
	SurveyTextResponse.__table__.create(bind=engine, checkfirst=True)
	RatingResponse.__table__.create(bind=engine, checkfirst=True)
	EmotionPreference.__table__.create(bind=engine, checkfirst=True)
