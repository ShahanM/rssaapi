import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from data.schemas.base_schemas import BaseDBSchema
from data.schemas.step_page_schemas import StepPagePreviewSchema


class StudyStepCreateSchema(BaseModel):
	name: str
	description: str
	order_position: int
	study_id: uuid.UUID


class StudyStepSchema(BaseDBSchema):
	name: str
	description: str
	order_position: int
	date_created: Optional[datetime]
	study_id: uuid.UUID

	def __hash__(self):
		return self.model_dump_json().__hash__()


class StudyStepDetailSchema(StudyStepSchema):
	pages: List[StepPagePreviewSchema]


class NextStepRequest(BaseModel):
	current_step_id: uuid.UUID
