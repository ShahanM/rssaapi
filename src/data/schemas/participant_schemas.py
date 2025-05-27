import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ParticipantCreateSchema(BaseModel):
	participant_type: uuid.UUID
	study_id: uuid.UUID
	external_id: str
	current_step: uuid.UUID
	current_page: Optional[uuid.UUID]


class ParticipantSchema(BaseModel):
	id: uuid.UUID
	participant_type: uuid.UUID
	external_id: str
	study_id: uuid.UUID
	condition_id: uuid.UUID
	current_status: str
	current_step: uuid.UUID
	current_page: Optional[uuid.UUID]
	date_created: Optional[datetime]
	date_updated: Optional[datetime]

	class Config:
		from_attributes = True
		json_encoders = {uuid.UUID: lambda v: str(v), datetime: lambda v: v.isoformat()}

	def __hash__(self):
		return self.model_dump_json().__hash__()


class ParticipantUpdateSchema(BaseModel):
	id: uuid.UUID
	participant_type: Optional[uuid.UUID]
	external_id: Optional[str]
	study_id: uuid.UUID
	condition_id: Optional[uuid.UUID]
	current_status: Optional[str]
	current_step: Optional[uuid.UUID]
	current_page: Optional[uuid.UUID]
