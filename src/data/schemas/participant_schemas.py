import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# TODO: Add documentation string all the schema
class ParticipantCreateSchema(BaseModel):
	participant_type: uuid.UUID = Field(
		default=uuid.UUID('149078d0-cece-4b2c-81cd-a7df4f76d15a'),
		description="""
		The UUID identifying the type of participant.
		""",
	)
	external_id: str = Field(
		default='Test Participant',
		description="""
		This is a convenient string to track participants that are redirected from a participant recruiting platform.
		The original intention is to store the participant's id in the referring platform.
		""",
	)
	current_step: uuid.UUID
	current_page: Optional[uuid.UUID]


class ParticipantSchema(BaseModel):
	id: uuid.UUID
	participant_type: uuid.UUID = Field(examples=[uuid.UUID('149078d0-cece-4b2c-81cd-a7df4f76d15a')], description='')
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
	study_id: uuid.UUID

	participant_type: Optional[uuid.UUID] = Field(
		examples=[uuid.UUID('149078d0-cece-4b2c-81cd-a7df4f76d15a')], description=''
	)
	external_id: Optional[str]
	condition_id: Optional[uuid.UUID]
	current_status: Optional[str]
	current_step: Optional[uuid.UUID]
	current_page: Optional[uuid.UUID]


class DemographicsCreateSchema(BaseModel):
	participant_id: uuid.UUID
	age_range: str
	gender: str
	race: list[str]
	education: str
	country: str
	state_region: Optional[str]
	gender_other: Optional[str]
	race_other: Optional[str]

	def model_dump(self, **kwargs):
		data = super().model_dump(**kwargs)
		data['race'] = ';'.join(self.race)
		del data['participant_id']
		return data
