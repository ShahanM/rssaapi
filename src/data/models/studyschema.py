from datetime import datetime
from typing import List

from pydantic import BaseModel


class QuestionScema(BaseModel):
    id: int
    page_id: int
    question_order: int
    question: str

    class Config:
        orm_mode = True


class PageSchema(BaseModel):
    id: int
    step_id: int
    page_order: int
    page_name: int

    questions: List[QuestionScema]

    class Config:
        orm_mode = True


class StepSchema(BaseModel):
    id: int
    study_id: int
    step_order: int
    step_name: str
    step_description: str

    pages: List[PageSchema]

    class Config:
        orm_mode = True


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
