import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from data.schemas.base_schemas import BaseDBSchema
from data.schemas.step_page_schemas import StepPagePreviewSchema


class StudyStepCreateSchema(BaseModel):
	name: str
	step_type: Optional[str]
	description: str
	study_id: uuid.UUID


class StudyStepSchema(BaseDBSchema):
	name: str = Field(
		...,
		description='The name of the step.',
		examples=['Welcome and Consent'],
	)
	description: str = Field(
		...,
		description='A small description for the step, to help in administration.',
		examples=['Step consisting of the welcome information and informed consent form.'],
	)

	step_type: Optional[str] = None

	title: Optional[str] = None
	instructions: Optional[str] = None

	order_position: int

	date_created: Optional[datetime]
	study_id: uuid.UUID

	def __hash__(self):
		return self.model_dump_json().__hash__()


class StudyStepDetailSchema(StudyStepSchema):
	pages: list[StepPagePreviewSchema]


class NextStepRequest(BaseModel):
	current_step_id: uuid.UUID


# class StepsReorderItem(BaseModel):
# 	id: uuid.UUID
# 	order_position: int


# class StepsReorderRequestSchema(BaseModel):
# 	reordered_steps: list[StepsReorderItem]
