import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.models.rssa_base_models import BaseModelMixin, DBBaseModel, DBBaseParticipantResponseModel


class ParticipantType(DBBaseModel):
    __tablename__ = 'participant_types'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column()


class StudyParticipant(BaseModelMixin, DBBaseModel):
    __tablename__ = 'study_participants'

    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    discarded: Mapped[bool] = mapped_column(default=False)

    participant_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('participant_types.id'), nullable=False)
    external_id: Mapped[str] = mapped_column()
    condition_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_conditions.id'), nullable=False)
    current_status: Mapped[str] = mapped_column(default='active')

    current_step_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_steps.id'), nullable=False)
    current_page_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('step_pages.id'), nullable=True)

    participant_session: Mapped['ParticipantSession'] = relationship(
        'ParticipantSession', back_populates='participant', cascade='all, delete-orphan'
    )


class Demographic(BaseModelMixin, DBBaseModel):
    __tablename__ = 'demographics'

    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_participants.id'))
    age_range: Mapped[str] = mapped_column()
    gender: Mapped[str] = mapped_column()
    gender_other: Mapped[Optional[str]] = mapped_column()
    race: Mapped[str] = mapped_column()
    race_other: Mapped[Optional[str]] = mapped_column()
    education: Mapped[str] = mapped_column()
    country: Mapped[str] = mapped_column()
    state_region: Mapped[Optional[str]] = mapped_column()

    version: Mapped[int] = mapped_column()
    discarded: Mapped[bool] = mapped_column(default=False)


class ParticipantSession(DBBaseModel):
    __tablename__ = 'participant_sessions'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_participants.id'))
    resume_code: Mapped[str] = mapped_column()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    participant: Mapped['StudyParticipant'] = relationship('StudyParticipant', back_populates='participant_session')


class ParticipantRecommendationContext(BaseModelMixin, DBBaseParticipantResponseModel):
    __tablename__ = 'participant_recommendation_context'

    recommendations_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint('study_id', 'participant_id', 'context_tag', name='uq_study_participant_rec_context'),
    )
