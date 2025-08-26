import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from data.schemas.study_condition_schemas import StudyConditionSchema
from data.schemas.study_step_schemas import StudyStepSchema


class StudyCreateSchema(BaseModel):
	"""
	Schema for creating a new study.
	"""

	name: str
	description: str


class StudySchema(BaseModel):
	"""
	Schema for study.
	"""

	id: uuid.UUID
	name: str
	description: Optional[str]

	date_created: Optional[datetime.datetime]
	created_by: Optional[str]
	owner: Optional[str]

	enabled: bool

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class StudyDetailSchema(BaseModel):
	"""
	Schema for study details with steps and conditions.
	"""

	id: uuid.UUID
	name: str
	description: str

	date_created: datetime.datetime
	created_by: Optional[str]
	owner: Optional[str]

	steps: list[StudyStepSchema]
	conditions: list[StudyConditionSchema]

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class StudyAuthSchema(BaseModel):
	id: uuid.UUID
	date_created: datetime.datetime

	model_config = ConfigDict(from_attributes=True)


class ConditionCountSchema(BaseModel):
	condition_id: uuid.UUID
	condition_name: str
	participant_count: int


class StudySummarySchema(BaseModel):
	study_id: uuid.UUID = Field(alias='id')
	name: str
	description: str
	date_created: datetime.datetime
	created_by: Optional[str]
	owner: Optional[str]

	total_participants: Optional[int]
	participants_by_condition: list[ConditionCountSchema]

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}

	@model_validator(mode='after')
	def compute_study_metrics(self):
		# TODO: Show other metrics such as time active or last response
		return self


class StudyConfigComponentSchema(BaseModel):
	name: str
	id: uuid.UUID

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class StudyConfigSchema(BaseModel):
	study_id: uuid.UUID
	study_steps: list[StudyConfigComponentSchema]
	conditions: dict[uuid.UUID, str]

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}
