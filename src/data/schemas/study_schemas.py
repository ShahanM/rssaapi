import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .study_condition_schemas import StudyConditionSchema


class StudyCreateSchema(BaseModel):
	"""
	Schema for creating a new study.
	"""

	name: str
	description: str


class StudySchema(BaseModel):
	"""
	Schema for study details.
	"""

	id: uuid.UUID
	name: str
	description: Optional[str]

	date_created: Optional[datetime.datetime]
	created_by: Optional[str]
	owner: Optional[str]

	class Config:
		orm_mode = True
		model_config = ConfigDict(from_attributes=True)


class StudyDetailSchema(BaseModel):
	"""
	Schema for study details with conditions.
	"""

	id: uuid.UUID
	name: str
	description: str

	date_created: datetime.datetime
	created_by: str
	owner: str

	conditions: list[StudyConditionSchema]

	class Config:
		orm_mode = True
		model_config = ConfigDict(from_attributes=True)


class StudyAuthSchema(BaseModel):
	id: uuid.UUID
	date_created: datetime.datetime

	model_config = ConfigDict(from_attributes=True)
