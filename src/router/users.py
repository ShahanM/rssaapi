from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.utils import *
from data.userdatabase import SessionLocal
from data.models.userschema import *
from data.users import *
from data.models.schema import RatedItemSchema, EmotionDiscreteInputSchema

from util.docs_metadata import TagsMetadataEnum as Tags
from .admin import get_current_active_user, AdminUser

router = APIRouter()

# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/user/create_db/", tags=[Tags.admin])
async def create_db(db: Session = Depends(get_db), \
    current_user: AdminUser = Depends(get_current_active_user)):
    """
    Create the database for the user data.
    
    This is only available to admin users.

    Returns a message indicating whether the database was created or not.
    """

    create_database(db)
    return "Database created"


@router.post('/user/consent/', response_model=UserSchema, tags=['user'])
async def create_new_user(newuser: NewUserSchema, \
    db: Session = Depends(get_db)):
    """
    Create a new user in the database.
    
    This is automatically created when a user consents to the study.
    An informed consent form must be signed by the user.

    Returns the user object if the user was successfully created, None 
    otherwise.
    """
    
    user = create_user(db, newuser)
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
