import uuid
from datetime import datetime

from pydantic import BaseModel

from data.schemas.base_schemas import BaseDBSchema


class StepPageCreateSchema(BaseModel):
	study_id: uuid.UUID
	step_id: uuid.UUID
	order_position: int
	name: str
	description: str


class StepPageSchema(BaseDBSchema):
	study_id: uuid.UUID
	step_id: uuid.UUID
	order_position: int
	name: str
	description: str
	date_created: datetime


class StepPageDetailSchema(StepPageSchema):
	pass


class StepPagePreviewSchema(BaseDBSchema):
	name: str
	order_position: int
