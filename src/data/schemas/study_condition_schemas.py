import uuid

from pydantic import BaseModel, ConfigDict


class StudyConditionCreateSchema(BaseModel):
	name: str
	description: str
	study_id: uuid.UUID


class StudyConditionSchema(BaseModel):
	"""
	Schema for study condition details.
	"""

	id: str
	name: str
	description: str
	study_id: uuid.UUID

	class Config:
		orm_mode = True
		model_config = ConfigDict(from_attributes=True)
