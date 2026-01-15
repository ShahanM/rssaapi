"""Schemas for participant responses."""

import uuid
from typing import Any

from pydantic import BaseModel

from rssa_api.data.schemas.base_schemas import DBMixin, VersionMixin


class ParticipantResponseContextMixin:
    """Mixin for participant response context."""

    __abstract__ = True
    study_step_id: uuid.UUID
    study_step_page_id: uuid.UUID | None = None
    context_tag: str


class ParticipantSurveyResponseBase(BaseModel, ParticipantResponseContextMixin):
    """Base schema for participant survey response."""

    survey_construct_id: uuid.UUID
    survey_item_id: uuid.UUID
    survey_scale_id: uuid.UUID
    survey_scale_level_id: uuid.UUID


class ParticipantSurveyResponseCreate(ParticipantSurveyResponseBase):
    """Schema for creating a participant survey response."""

    pass


class ParticipantSurveyResponseRead(ParticipantSurveyResponseBase, VersionMixin, DBMixin):
    """Schema for reading a participant survey response."""

    pass


class ParticipantSurveyResponseUpdate(ParticipantSurveyResponseRead):
    """Schema for updating a participant survey response."""

    survey_scale_level_id: uuid.UUID


class ParticipantFreeformResponseBase(BaseModel, ParticipantResponseContextMixin):
    """Base schema for participant freeform response."""

    response_text: str


class ParticipantFreeformResponseCreate(ParticipantFreeformResponseBase):
    """Schema for creating a participant freeform response."""

    pass


class ParticipantFreeformResponseRead(ParticipantFreeformResponseBase, VersionMixin, DBMixin):
    """Schema for reading a participant freeform response."""

    pass


class ParticipantFreeformResponseUpdate(ParticipantFreeformResponseRead):
    """Schema for updating a participant freeform response."""

    response_text: str


class RatedItem(BaseModel):
    """Schema for a rated item."""

    item_id: uuid.UUID
    rating: int


class ParticipantRatingBase(BaseModel, ParticipantResponseContextMixin):
    """Base schema for participant rating."""

    rated_item: RatedItem


class MovieLensRating(BaseModel):
    """Schema for MovieLens rating."""

    item_id: str | int
    rating: int


class DynamicPayload(BaseModel):
    """Schema for dynamic payload with extra fields."""

    experimnet_condition: str | None = None
    extra: dict[str, Any] = {}

    model_config = {'extra': 'allow'}


class ParticipantStudyInteractionResponseBase(BaseModel):
    """Base schema for participant study interaction response."""

    payload_json: DynamicPayload


class ParticipantStudyInteractionResponseCreate(
    ParticipantStudyInteractionResponseBase, ParticipantResponseContextMixin
):
    """Schema for creating a participant study interaction response."""

    pass


class ParticipantStudyInteractionResponseRead(ParticipantStudyInteractionResponseCreate, VersionMixin, DBMixin):
    """Schema for reading a participant study interaction response."""

    pass


class ParticipantStudyInteractionResponseUpdate(ParticipantStudyInteractionResponseBase, DBMixin, VersionMixin):
    """Schema for updating a participant study interaction response."""

    pass


# The Feedback Schemas are deprecated. They will be refactored to become user feedback. Participant feedback will
# be collected in the form of freeform responses. So we will keep them as is for now.
class FeedbackBaseSchema(BaseModel, ParticipantResponseContextMixin):
    """Base schema for feedback."""

    feedback_text: str
    feedback_type: str
    feedback_category: str


class FeedbackSchema(FeedbackBaseSchema, VersionMixin, DBMixin):
    """Schema for feedback with DB mixin."""

    pass


class ParticipantRatingRead(ParticipantRatingBase, VersionMixin, DBMixin):
    """Schema for reading a participant rating."""

    pass


class ParticipantRatingUpdate(VersionMixin, DBMixin):
    """Schema for updating a participant rating."""

    rated_item: RatedItem
