from datetime import datetime
from typing import List

from pydantic import BaseModel


class QuestionSchema(BaseModel):
    id: int | None
    page_id: int | None
    question_order: int | None
    question: str | None

    class Config:
        orm_mode = True


class NewQuestionSchema(BaseModel):
	question_order: int
	questiontxt: str


class PageSchema(BaseModel):
    id: int | None
    step_id: int | None
    page_order: int | None
    page_name: str | None

    questions: List[QuestionSchema]

    class Config:
        orm_mode = True


class NewPageSchema(BaseModel):
	page_order: int
	page_name: str


class StepSchema(BaseModel):
    id: int | None
    study_id: int | None
    step_order: int | None
    step_name: str | None
    step_description: str | None

    pages: List[PageSchema]

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

    steps: List[StepSchema]
    conditions: List[StudyConditionSchema]

    class Config:
        orm_mode = True
