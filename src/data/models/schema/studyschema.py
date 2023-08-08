from datetime import datetime
from typing import List, Union

from pydantic import BaseModel


class QuestionSchema(BaseModel):
	id: Union[int, None]
	page_id: Union[int, None]
	question_order: Union[int, None]
	question: Union[str, None]

	class Config:
		orm_mode = True


class NewQuestionSchema(BaseModel):
	question_order: int
	questiontxt: str


class PageSchema(BaseModel):
	id: Union[int, None]
	step_id: Union[int, None]
	page_order: Union[int, None]
	page_name: Union[str, None]
	page_instruction: Union[str, None]

	questions: List[QuestionSchema]

	class Config:
		orm_mode = True


class NewPageSchema(BaseModel):
	page_order: int
	page_name: str
	page_instruction: str


class StepSchema(BaseModel):
	id: Union[int, None]
	study_id: Union[int, None]
	step_order: Union[int, None]
	step_name: Union[str, None]
	step_description: Union[str, None]

	# pages: List[PageSchema]

	class Config:
		orm_mode = True


class NewStepSchema(BaseModel):
	step_order: int
	step_name: str
	step_description: str


class StudyConditionSchema(BaseModel):
	id: int
	study_id: int
	condition_name: str

	class Config:
		orm_mode = True


class StudySchema(BaseModel):
	id: int
	date_created: datetime
	study_name: str

	# steps: List[StepSchema]
	conditions: List[StudyConditionSchema]

	class Config:
		orm_mode = True


class NewConditionSchema(BaseModel):
	condition_name: str
