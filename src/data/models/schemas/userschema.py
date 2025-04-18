from typing import List, Optional, Union

from pydantic import BaseModel

from .movieschema import RatedItemSchema


class UserTypeSchema(BaseModel):
	id: int
	type_str: str

	class Config:
		from_attributes = True


class UserSchema(BaseModel):
	id: int

	study_id: int
	condition: int
	completed: bool
	user_type: UserTypeSchema

	seen_items: List[int]

	class Config:
		from_attributes = True


class NewUserSchema(BaseModel):
	study_id: int
	user_type: str


class NewQuestionResponseSchema(BaseModel):
	question_id: int
	response: Union[int, str]


class NewSurveyResponseSchema(BaseModel):
	user_id: int
	study_id: int
	page_id: int

	responses: List[NewQuestionResponseSchema]


class RatingResponseSchema(BaseModel):
	user_id: int
	study_id: int
	page_id: int
	page_level: int

	ratings: List[RatedItemSchema]


class SelectionResponseSchema(BaseModel):
	user_id: int
	study_id: int
	page_id: int
	selected_item: RatedItemSchema


class SeenItemsSchema(BaseModel):
	user_id: int
	page_id: int
	page_level: int
	items: List[int]


class SeenItemSchema(BaseModel):
	user_id: int
	page_id: int
	page_level: int
	item_id: int

	class Config:
		from_attributes = True


class EmotionPreferenceSchema(BaseModel):
	user_id: int
	anger: float
	anticipation: float
	disgust: float
	fear: float
	joy: float
	surprise: float
	sadness: float
	trust: float

	class Config:
		from_attributes = True


class NewSurveyTextResponseSchema(BaseModel):
	user_id: int
	study_id: int
	page_id: int

	responses: List[NewQuestionResponseSchema]


class InteractionLogSchema(BaseModel):
	user_id: int
	study_id: int
	step_id: int
	page_id: Optional[int]
	time_spent: int
	interaction_type: str
	interaction_target: str
	item_id: Optional[int]
	rating: Optional[int]

	class Config:
		from_attributes = True


class DemographicInfoSchema(BaseModel):
	user_id: int
	study_id: int

	age_group: str
	gender: str
	education: str

	class Config:
		from_attributes = True
