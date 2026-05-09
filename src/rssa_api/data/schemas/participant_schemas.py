"""Schemas for study participants."""

import uuid
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, computed_field, field_serializer, field_validator

from .base_schemas import AuditMixin, DBMixin, DisplayInfoMixin, DisplayNameMixin
from .study_components import StudyConditionPresent


class StudyParticipantBase(BaseModel):
    """Base schema for study participant."""

    current_step_id: uuid.UUID
    current_page_id: uuid.UUID | None = None


class StudyParticipantCreate(BaseModel):
    """Schema for creating a study participant."""

    participant_type_key: str | None
    current_step_id: uuid.UUID
    current_page_id: uuid.UUID | None = None
    source_meta: dict[str, str] | None


class StudyParticipantRead(StudyParticipantBase, DBMixin):
    """Schema for reading a study participant."""

    study_id: uuid.UUID
    study_condition_id: uuid.UUID
    current_status: str

    model_config = ConfigDict(frozen=True)


class StudyParticipantTypeRead(BaseModel):
    """Schema for reading a study participant type."""

    id: uuid.UUID
    type: str

    model_config = {'from_attributes': True}


class StudyParticipantReadWithCondition(StudyParticipantRead):
    """Schema for reading a study participant with condition."""

    study_condition: StudyConditionPresent


class DemographicsBase(BaseModel):
    """Base schema for demographics."""

    age_range: str | None = None
    gender: str | None = None
    race: list[str] | None = None
    education: str | None = None
    country: str | None = None
    state_region: str | None = None
    gender_other: str | None = None
    race_other: str | None = None
    urbanicity: str | None = None
    raw_json: dict | None = None

    @field_validator('race', mode='before')
    @classmethod
    def handle_raw_data(cls, value: Any) -> list[str] | None:
        if isinstance(value, str):
            return [race_opt.strip() for race_opt in value.split(';')]
        return value

    @field_serializer('race')
    def serialize_race(self, race: list[str] | None, _info) -> str | None:
        """Serializes the race list back into a semicolon-separated string for the DB."""
        if not race:
            return None
        return ';'.join(race)


class DemographicsCreate(DemographicsBase):
    """Schema for creating demographics."""

    model_config = {'from_attributes': True}


class DemographicsUpdate(BaseModel):
    """Schema to help the upsert with partial data."""

    age_range: str | None = None
    gender: str | None = None
    gender_other: str | None = None
    race: list[str] | None = None
    race_other: str | None = None
    education: str | None = None
    country: str | None = None
    state_region: str | None = None
    urbanicity: str | None = None


class StudyAttentionCheckMinimalRead(BaseModel):
    id: uuid.UUID
    expected_survey_scale_level_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ParticipantAttentionCheckResponseAudit(BaseModel):
    id: uuid.UUID
    study_attention_check_id: uuid.UUID
    responded_survey_scale_level_id: uuid.UUID | None

    study_attention_check: StudyAttentionCheckMinimalRead

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def passed_attention(self) -> bool:
        if not self.responded_survey_scale_level_id:
            print('NOTHING TO REPORT')
            return False
        return self.responded_survey_scale_level_id == self.study_attention_check.expected_survey_scale_level_id


class ParticipantAuditRead(DBMixin, AuditMixin, DisplayNameMixin, DisplayInfoMixin):
    id: uuid.UUID
    current_status: str | None = 'active'

    _display_name_source_field: ClassVar[str] = 'id'
    _display_info_source_field: ClassVar[str] = 'current_status'

    source_meta: str | None
    attention_check_responses: list[ParticipantAttentionCheckResponseAudit] = []

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def all_attention_checks_passed(self) -> bool:
        if not self.attention_check_responses:
            return False
        return all(check.passed_attention for check in self.attention_check_responses)
