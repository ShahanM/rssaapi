from typing import List, Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from compute.utils import *
# from data.userdatabase import SessionLocal
from data.models.studyschema import StudySchema
from data.userdatabase import get_user_db, create_database_meta
from data.models.userschema import *
from data.users import *
from data.models.movieschema import RatedItemSchema, EmotionDiscreteInputSchema

from util.docs_metadata import TagsMetadataEnum as Tags
from .admin import get_current_active_user, AdminUser
from .study import get_db as study_db
from data.studies import get_count_of_questions_by_study_id
from data.studies import get_study_by_id

router = APIRouter()

# async def verify_token(x_token: Annotated[str, Header()]):
#     if x_token != "fake-super-secret-token":
#         raise HTTPException(status_code=400, detail="X-Token header invalid")


async def get_current_study(study_id: Annotated[int, Header()], \
	db: Session = Depends(study_db)):
	if study_id is None:
		raise HTTPException(status_code=400, detail="Study ID not provided")
	study = get_study_by_id(db, study_id)

	if study is None:
		raise HTTPException(status_code=400, detail="Study ID not found")
	
	return study

async def get_db(study: StudySchema = Depends(get_current_study)):
	# db = SessionLocal()
	db = get_user_db(study.id)
	try:
		yield db
	finally:
		db.close()


# rom typing import Annotated

# from fastapi import Depends, FastAPI, Header, HTTPException

# app = FastAPI()


# async def verify_token(x_token: Annotated[str, Header()]):
#     if x_token != "fake-super-secret-token":
#         raise HTTPException(status_code=400, detail="X-Token header invalid")


# async def verify_key(x_key: Annotated[str, Header()]):
#     if x_key != "fake-super-secret-key":
#         raise HTTPException(status_code=400, detail="X-Key header invalid")
#     return x_key


# @app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
# async def read_items():
#     return [{"item": "Foo"}, {"item": "Bar"}]


@router.post("/user/create_db/", tags=[Tags.admin], \
	dependencies=[Depends(get_current_study), Depends(get_current_active_user)])
async def create_db(study_id: int):
	"""
	Create the database for the user data.
	
	This is only available to admin users.

	Returns a message indicating whether the database was created or not.
	"""

	# create_database(study_id)
	create_database_meta(study_id)
	return "Database created"


@router.post('/user/consent/', response_model=UserSchema, tags=['user'])
async def create_new_user(newuser: NewUserSchema, \
	db: Session = Depends(get_db), study: StudySchema = Depends(get_current_study)):
	"""
	Create a new user in the database.
	
	This is automatically created when a user consents to the study.
	An informed consent form must be signed by the user.

	Returns the user object if the user was successfully created, None 
	otherwise.
	"""
	condition_id = random.choice(study.conditions).id
	user = create_user(db, newuser, condition_id)
	return user


@router.post('/user/consent/{condition_id}/', response_model=UserSchema, tags=['user'])
async def create_new_test_user(condition_id: int, newuser: NewUserSchema, \
	db: Session = Depends(get_db)):
	"""
	Create a new user in the database.
	
	This is automatically created when a user consents to the study.
	An informed consent form must be signed by the user.

	Returns the user object if the user was successfully created, None 
	otherwise.
	"""
	
	user = create_user(db, newuser, condition_id)
	return user


@router.put('/user/{user_id}/response/{type}/', response_model=bool, \
	tags=['user'])
async def create_new_response(user_id: int, type: str, \
	response: NewSurveyResponseSchema, db: Session = Depends(get_db)):
	"""
	Create a new response for specified user in the database.

	Responses can either be a likert scale or free text.

	- **type**: str can be either 'likert' or 'freetext'.
	- **response**: NewSurveyResponseSchema consists of all the 
	responses for a page.

	Returns True if the response was successfully created, False otherwise.

	"""
	if type == 'likert':
		res = create_survey_response(db, user_id, response)
		if res:
			return True
		else:
			return False
	elif type == 'freetext':
		res = create_survey_text_response(db, user_id, response)
		if res:
			return True
		else:
			return False

	# TODO: Add other types of responses (free text)


@router.put('/user/{user_id}/itemrating/', \
	response_model=List[RatedItemSchema], tags=['user'])
async def create_item_ratings(user_id: int, ratings: RatingResponseSchema, \
	db: Session = Depends(get_db)):
	"""
	Create a new rating response for specified user in the database.

	- **ratings**: RatingResponseSchema consists of all the items rated by the 
	user.

	Returns a list of RatedItemSchema objects if the response was successfully 
	created, None otherwise.
	"""
	rateditems = create_rating_response(db, user_id, ratings)

	return rateditems


@router.put('/user/{user_id}/seenitems/', response_model=List[SeenItemSchema], \
	tags=['user'])
async def add_seen_items(user_id, items: SeenItemsSchema, \
	db: Session = Depends(get_db)):
	"""
	Add items to the list of seen items for specified user in the database.

	- **items**: SeenItemsSchema consists of all the items that appear on any 
	page that the user can interact with.

	Returns a list of SeenItemSchema objects if the response was successfully 
	created, None otherwise.    
	"""
	seenitems = create_seen_items_if_not_exist(db, user_id, items)

	return seenitems


@router.put('/user/{user_id}/emotionprefs/', \
	response_model=EmotionPreferenceSchema, tags=['user'])
async def create_emotion_preference_response(user_id: int, \
	emoinput: List[EmotionDiscreteInputSchema], db: Session = Depends(get_db)):
	"""
	Create a new emotion preference response for specified user in the database.

	- **emoinput**: EmotionDiscreteInputSchema consists of the final emotion
	preference for the user.

	Returns an EmotionPreferenceSchema object if the response was successfully
	"""
	res = create_emotion_preference(db, user_id, emoinput)

	return res


@router.put('/user/{user_id}/itemselect/', response_model=RatedItemSchema, \
	tags=['user'])
async def create_selected_item(user_id: int, \
	selection: SelectionResponseSchema, db: Session = Depends(get_db)):
	"""
	Update the item selected by the user in the database.

	- **selection**: RatedItemSchema consists of the item selected by the user.

	Returns a RatedItemSchema object if the response was successfully
	"""

	res = create_item_selection(db, user_id, selection)

	return res


@router.put('/user/{user_id}/demographicInfo/', response_model=int, \
	tags=['user'])
async def create_demographic_info(demo: DemographicInfoSchema, \
	db: Session = Depends(get_db)):
	"""
	Create a new demographic info response for specified user in the database.

	- **demo**: DemogrphicsInfoSchema consists of the demographic info for the user.

	Returns the id of a DemogrphicsInfoSchema object if the response was
	successfully created, None otherwise.
	"""

	demoid = create_demographic_info_response(db, demo)

	return demoid


@router.put('/user/{user_id}/log/', response_model=int, \
	tags=['user'])
async def create_interaction_log(log: InteractionLogSchema, db: Session = Depends(get_db)):
	"""
	Create a new interaction log for specified user in the database.

	Returns the id of an InteractionLogSchema object if the response was 
	successfully created, None otherwise.

	Note: This is not a RESTful API endpoint. It is used by the frontend to
	log user interactions. It is also supposed to fail silently and be
	non-blocking.
	"""

	logid = log_interaction(db, log)

	return logid


@router.get('/user/{user_id}/completion', tags=['user'])
async def get_completion_url(user_id: int, db: Session = Depends(get_db), \
	studydb: Session = Depends(study_db), \
	study: StudySchema = Depends(get_current_study)):
	"""
	Get the completion code for the user.
	"""
	# FIXME: This is weird coupling. We should not be using the study db here.
	qcount = get_count_of_questions_by_study_id(studydb, study.id)
	# TODO: Create a completion rubric for the study and use it here.

	completed = validate_study_completion(db, user_id, qcount)
	print(completed)
	if(completed):
		# FIXME: This should not be hardcoded but instead be a part of the study
		return {
			'status': 'completed',
			'completion_url': 'https://app.prolific.co/submissions/complete?cc=CYIWLLZU'
		}

	return {
		'status': 'incomplete',
		'completion_url': None
	}
