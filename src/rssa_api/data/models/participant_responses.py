"""Models for participant responses within studies.

This file included feedback, survey item responses,
freeform responses, ratings, and interaction logs.
"""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.models.rssa_base_models import (
    BaseModelMixin,
    DBBaseParticipantResponseModel,
)
from rssa_api.data.models.survey_constructs import SurveyScaleLevel


# TODO: This table will be removed from the participant response flow. It will be used for testing and dev feedback.
# In the future, to disentable feedback from participant responses, the sutdy_participant_id foreign key needs to be
# dropped, and should be replaced with a text field for email or user identifier.
class Feedback(BaseModelMixin, DBBaseParticipantResponseModel):
    """Stores participant feedback for a study.

    Attributes:
        feedback_text (str): The text of the feedback provided by the participant.
        feedback_type (str): The type/category of feedback (e.g., bug report, suggestion).
        feedback_category (str): The broader category of feedback (e.g., usability, content).
    """

    __tablename__ = 'feedbacks'

    feedback_text: Mapped[str] = mapped_column(nullable=False)
    feedback_type: Mapped[str] = mapped_column(nullable=False)
    feedback_category: Mapped[str] = mapped_column(nullable=False)


class ParticipantSurveyResponse(BaseModelMixin, DBBaseParticipantResponseModel):
    """Stores participant responses to specific survey items within the context of a survey construct."""

    __tablename__ = 'participant_survey_responses'

    survey_construct_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_constructs.id'), nullable=False)
    survey_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_items.id'), nullable=True)
    survey_scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_scales.id'), nullable=True)
    survey_scale_level_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('survey_scale_levels.id'))

    survey_scale_level: Mapped[Optional['SurveyScaleLevel']] = relationship()

    __table_args__ = (UniqueConstraint('study_id', 'study_participant_id', 'survey_item_id', name='uq_survey_context'),)


class ParticipantFreeformResponse(BaseModelMixin, DBBaseParticipantResponseModel):
    """Stores participant freeform text responses within the study context."""

    __tablename__ = 'participant_freeform_responses'

    response_text: Mapped[str] = mapped_column()

    __table_args__ = (UniqueConstraint('study_id', 'study_participant_id', 'context_tag', name='uq_freeform_context'),)


class ParticipantRating(BaseModelMixin, DBBaseParticipantResponseModel):
    """Stores participant ratings for various content within the study."""

    __tablename__ = 'participant_ratings'

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    item_table_name: Mapped[str] = mapped_column()
    rating: Mapped[int] = mapped_column()
    scale_min: Mapped[int] = mapped_column()
    scale_max: Mapped[int] = mapped_column()

    @property
    def rated_item(self) -> dict:
        """Returns the rated item as a dictionary for schema validation."""
        return {'item_id': self.item_id, 'rating': self.rating}


class ParticipantInteractionLog(BaseModelMixin, DBBaseParticipantResponseModel):
    """Stores general participant interaction events/behaviors within the study."""

    __tablename__ = 'participant_interaction_logs'

    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint('study_id', 'study_participant_id', 'context_tag', name='uq_interaction_context_tag'),
    )


class ParticipantStudyInteractionResponse(BaseModelMixin, DBBaseParticipantResponseModel):
    """Stores participant responses to study interaction prompts."""

    __tablename__ = 'participant_study_interaction_responses'

    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint('study_id', 'study_participant_id', 'context_tag', name='uq_study_participant_context_tag'),
    )
