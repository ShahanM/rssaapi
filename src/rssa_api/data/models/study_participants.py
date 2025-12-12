"""SQLAlchemy models for study participants and related entities."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.models.rssa_base_models import BaseModelMixin, DBBaseModel, DBBaseParticipantResponseModel


class StudyParticipantType(DBBaseModel):
    """SQLAlchemy model for the 'study_participant_types' table.

    Attributes:
        id: Primary key.
        type: Type of participant (e.g., 'student', 'professional').
    """

    __tablename__ = 'study_participant_types'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column()


class StudyParticipant(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'study_participants' table.

    Attributes:
        study_id: Foreign key to the study.
        discarded: Indicates if the participant is discarded.
        study_participant_type_id: Foreign key to the participant type.
        external_id: External identifier for the participant.
        study_condition_id: Foreign key to the study condition.
        current_status: Current status of the participant (e.g., 'active', 'completed').
        current_step_id: Foreign key to the current study step.
        current_page_id (Optional[uuid.UUID]): Foreign key to the current step page.
    """

    __tablename__ = 'study_participants'

    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    discarded: Mapped[bool] = mapped_column(default=False)

    study_participant_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_participant_types.id'), nullable=False)
    external_id: Mapped[str] = mapped_column()
    study_condition_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_conditions.id'), nullable=False)
    current_status: Mapped[str] = mapped_column(default='active')

    current_step_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_steps.id'), nullable=False)
    current_page_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('study_step_pages.id'), nullable=True)

    participant_study_session: Mapped['ParticipantStudySession'] = relationship(
        'ParticipantStudySession', back_populates='study_participant', cascade='all, delete-orphan'
    )
    study_condition: Mapped['StudyCondition'] = relationship('StudyCondition', back_populates='study_participants') 


class Demographic(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'demographics' table.

    Attributes:
        study_participant_id: Foreign key to the study participant.
        age_range: Age range of the participant.
        gender: Gender of the participant.
        gender_other: Other gender specification.
        race: Race of the participant.
        race_other: Other race specification.
        education: Education level of the participant.
        country: Country of residence.
        state_region: State or region of residence.
        version: Version of the demographic record.
        discarded: Indicates if the demographic record is discarded.
    """

    __tablename__ = 'participant_demographics'

    study_participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_participants.id'))
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


class ParticipantStudySession(DBBaseModel):
    """SQLAlchemy model for the 'participant_sessions' table.

    Attributes:
        id: Primary key.
        created_at: Timestamp of creation.
        study_participant_id: Foreign key to the study participant.
        resume_code: Resume code for the participant session.
        expires_at: Expiration timestamp for the session.
        is_active: Indicates if the session is active.
    """

    __tablename__ = 'participant_study_sessions'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    study_participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_participants.id'))
    resume_code: Mapped[str] = mapped_column()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    study_participant: Mapped['StudyParticipant'] = relationship('StudyParticipant', back_populates='participant_study_session')


class ParticipantRecommendationContext(DBBaseParticipantResponseModel, BaseModelMixin):
    """SQLAlchemy model for the 'participant_recommendation_context' table.

    Attributes:
        recommendations_json: JSON field storing recommendation context data.
    """

    __tablename__ = 'participant_recommendation_context'

    recommendations_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint('study_id', 'study_participant_id', 'context_tag', name='uq_study_participant_rec_context'),
    )
