import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StudyConditionCreateSchema(BaseModel):
	name: str
	description: str
	study_id: uuid.UUID


class StudyConditionSchema(BaseModel):
	"""
	Schema for study condition details.
	"""

	id: uuid.UUID
	name: str
	description: str
	study_id: uuid.UUID

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}
