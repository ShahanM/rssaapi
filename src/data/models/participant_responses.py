import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import RSSADBBase as Base
from data.models.survey_constructs import ScaleLevel


class Feedback(Base):
    __tablename__ = 'feedbacks'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    feedback_text: Mapped[str] = mapped_column(nullable=False)
    feedback_type: Mapped[str] = mapped_column(nullable=False)
    feedback_category: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    version: Mapped[int] = mapped_column()

    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_participants.id'), nullable=False)
    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)


class SurveyItemResponse(Base):
    """
    Stores participant responses to specific, structured survey items.
    Replaces ParticipantSurveyResponse.
    """

    __tablename__ = 'survey_item_responses'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_participants.id'), nullable=False)
    construct_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_constructs.id'), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('construct_items.id'), nullable=True)
    scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('construct_scales.id'), nullable=True)
    scale_level_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('scale_levels.id'))

    # FIXME: response should be non null but for now it is nullable because of older data and a lack of default
    scale_level: Mapped[Optional['ScaleLevel']] = relationship()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    version: Mapped[int] = mapped_column()

    discarded: Mapped[bool] = mapped_column(default=False)

    # participant: Mapped['StudyParticipant'] = relationship('StudyParticipant', back_populates='survey_item_responses')
    # construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='item_responses')
    # item: Mapped['ConstructItem'] = relationship('ConstructItem', back_populates='responses')


class FreeformResponse(Base):
    """
    Stores participant's freeform text responses or comments provided
    within the context of a survey, step, or specific item (if applicable).
    This handles cases where construct_id/item_id might be null.
    """

    __tablename__ = 'freeform_responses'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_participants.id'), nullable=False)
    step_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey('study_steps.id'), nullable=True
    )  # Nullable if comment is for entire survey
    item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey('construct_items.id'), nullable=True
    )  # Nullable if not tied to specific item
    context_tag: Mapped[Optional[str]] = mapped_column()
    response_text: Mapped[str] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    version: Mapped[int] = mapped_column()

    discarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # participant: Mapped['StudyParticipant'] = relationship('StudyParticipant', back_populates='survey_freeform_responses')
    # step: Mapped['StudyStep'] = relationship('StudyStep', back_populates='freeform_responses')
    # item: Mapped['ConstructItem'] = relationship('ConstructItem', back_populates='freeform_responses')
