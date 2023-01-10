from typing import List, Optional, Literal, Union
from pydantic import BaseModel


class UserTypeSchema(BaseModel):
	id: int
	type_str: str

	class Config:
		orm_mode = True


class UserSchema(BaseModel):
	id: int

	condition:int
	user_type: UserTypeSchema
	
	seen_items: List[int]

	class Config:
		orm_mode = True


class NewUserSchema(BaseModel):
	condition: int
	user_type: str