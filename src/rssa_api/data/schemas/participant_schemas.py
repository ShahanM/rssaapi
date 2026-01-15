"""Schemas for study participants."""

import uuid

from pydantic import BaseModel, Field, field_validator

from .base_schemas import DBMixin
from .study_components import StudyConditionRead


class StudyParticipantBase(BaseModel):
    """Base schema for study participant."""

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
    current_page_id: uuid.UUID | None = None


class StudyParticipantCreate(BaseModel):
    """Schema for creating a study participant."""

    participant_type_key: str
    external_id: str
    current_step_id: uuid.UUID
    current_page_id: uuid.UUID | None = None


class StudyParticipantRead(StudyParticipantBase, DBMixin):
    """Schema for reading a study participant."""

    study_id: uuid.UUID
    study_condition_id: uuid.UUID
    current_status: str

    def __hash__(self):
        return self.model_dump_json().__hash__()


class StudyParticipantTypeRead(BaseModel):
    """Schema for reading a study participant type."""

    id: uuid.UUID
    key: str = Field(validation_alias='type')

    model_config = {'from_attributes': True}


class StudyParticipantReadWithCondition(StudyParticipantRead):
    """Schema for reading a study participant with condition."""

    study_condition: 'StudyConditionRead'
    participant_type: StudyParticipantTypeRead = Field(validation_alias='study_participant_type')


class DemographicsBase(BaseModel):
    """Base schema for demographics."""

    age_range: str
    gender: str
    race: list[str]
    education: str
    country: str
    state_region: str | None
    gender_other: str | None
    race_other: str | None

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
    """Schema for creating demographics."""

    model_config = {'from_attributes': True}
