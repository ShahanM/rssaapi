from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.utils import *
from data.userdatabase import SessionLocal
from data.models.userschema import UserSchema, NewUserSchema
from data.users import create_user, get_user, create_database

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
async def create_db(db: Session = Depends(get_db), current_user: AdminUser = Depends(get_current_active_user)):
	create_database(db)
	return "Database created"


@router.post('/user/consent/', response_model=UserSchema, tags=['user'])
async def create_new_user(newuser: NewUserSchema, db: Session = Depends(get_db)):
	user = create_user(db, newuser)
	return user
