import uuid
from typing import Optional

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.models.rssa_base_models import (
    BaseModelMixin,
    DBBaseParticipantResponseModel,
)
from data.models.survey_constructs import ScaleLevel


class Feedback(BaseModelMixin, DBBaseParticipantResponseModel):
    __tablename__ = 'feedbacks'

    feedback_text: Mapped[str] = mapped_column(nullable=False)
    feedback_type: Mapped[str] = mapped_column(nullable=False)
    feedback_category: Mapped[str] = mapped_column(nullable=False)
    __table_args__ = (UniqueConstraint('study_id', 'participant_id', 'context_tag', name='uq_feedbacks_context'),)


class SurveyItemResponse(BaseModelMixin, DBBaseParticipantResponseModel):
    """
    Stores participant responses to specific, structured survey items.
    Replaces ParticipantSurveyResponse.
    """

    __tablename__ = 'survey_item_responses'

    construct_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_constructs.id'), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('construct_items.id'), nullable=True)
    scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('construct_scales.id'), nullable=True)
    scale_level_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('scale_levels.id'))

    scale_level: Mapped[Optional['ScaleLevel']] = relationship()

    __table_args__ = (UniqueConstraint('study_id', 'participant_id', 'item_id', name='uq_survey_context'),)


class FreeformResponse(BaseModelMixin, DBBaseParticipantResponseModel):
    """
    Stores participant's freeform text responses or comments provided
    within the context of a survey, step, or specific item (if applicable).
    This handles cases where construct_id/item_id might be null.
    """

    __tablename__ = 'freeform_responses'

    item_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('construct_items.id'), nullable=True)
    response_text: Mapped[str] = mapped_column()

    __table_args__ = (UniqueConstraint('study_id', 'participant_id', 'context_tag', name='uq_freeform_context'),)


class ParticipantRating(BaseModelMixin, DBBaseParticipantResponseModel):
    """
    Stores participant ratings for various content within the study.
    """

    __tablename__ = 'participant_ratings'

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    item_table_name: Mapped[str] = mapped_column()
    rating: Mapped[int] = mapped_column()
    scale_min: Mapped[int] = mapped_column()
    scale_max: Mapped[int] = mapped_column()

    __table_args__ = (UniqueConstraint('study_id', 'participant_id', 'item_id', name='uq_participant_ratings_item'),)


class ParticipantInteractionLog(BaseModelMixin, DBBaseParticipantResponseModel):
    """
    Stores general participant interaction events/behaviors within the study.
    """

    __tablename__ = 'participant_interaction_logs'

    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (UniqueConstraint('study_id', 'participant_id', 'context_tag', name='uq_interaction_context_tag'),)


class StudyInteractionResponse(BaseModelMixin, DBBaseParticipantResponseModel):
    __tablename__ = 'study_interaction_responses'

    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint('study_id', 'participant_id', 'context_tag', name='uq_study_participant_context_tag'),
    )
