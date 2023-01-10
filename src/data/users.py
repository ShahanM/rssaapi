from sqlalchemy.orm import Session
from .models.user import User, UserType, SeenItem
from .models.userschema import NewUserSchema
from typing import List
from .userdatabase import engine

def create_user(db: Session, newuser: NewUserSchema) -> User:

	usertype = get_user_type_by_str(db, newuser.user_type)
	user = User(condition=newuser.condition, user_type=usertype)

	db.add(user)
	db.commit()
	db.refresh(user)

	return user

def get_user(db: Session, user_id: int) -> User:
	user = db.query(User).filter(User.user_id == user_id).first()
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


def create_database(base):
	UserType.__table__.create(bind=engine, checkfirst=True)
	User.__table__.create(bind=engine, checkfirst=True)
	SeenItem.__table__.create(bind=engine, checkfirst=True)