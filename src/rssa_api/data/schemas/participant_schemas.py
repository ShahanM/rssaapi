import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .base_schemas import DBMixin


class StudyParticipantBase(BaseModel):
    study_participant_type_id: uuid.UUID = Field(
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
    current_step_id: uuid.UUID
    current_page_id: Optional[uuid.UUID] = None


class StudyParticipantCreate(StudyParticipantBase):
    pass

class StudyParticipantRead(StudyParticipantBase, DBMixin):
    study_id: uuid.UUID
    condition_id: uuid.UUID
    current_status: str

    def __hash__(self):
        return self.model_dump_json().__hash__()


class DemographicsBase(BaseModel):
    age_range: str
    gender: str
    race: list[str]
    education: str
    country: str
    state_region: Optional[str]
    gender_other: Optional[str]
    race_other: Optional[str]

    @field_validator('race', mode='before')
    @classmethod
    def handle_raw_data(cls, value):
        if isinstance(value, str):
            return [race_opt.strip() for race_opt in value.split(';')]
        return value

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data['race'] = ';'.join(self.race)
        del data['participant_id']
        return data


class DemographicsCreate(DemographicsBase):
    model_config = {'from_attributes': True}
