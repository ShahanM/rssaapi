import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StudyStepCreateSchema(BaseModel):
	name: str
	description: str
	order_position: int
	study_id: uuid.UUID


class StudyStepSchema(BaseModel):
	id: uuid.UUID
	name: str
	description: str
	order_position: int
	date_created: Optional[datetime]
	study_id: uuid.UUID

	class Config:
		from_attributes = True
		json_encoders = {uuid.UUID: lambda v: str(v), datetime: lambda v: v.isoformat()}

	def __hash__(self):
		return self.model_dump_json().__hash__()


class NextStepRequest(BaseModel):
	current_step_id: uuid.UUID
