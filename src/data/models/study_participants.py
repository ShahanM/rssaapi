import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import RSSADBBase as Base


class ParticipantType(Base):
    __tablename__ = 'participant_types'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column()


class StudyParticipant(Base):
    __tablename__ = 'study_participants'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('participant_types.id'), nullable=False)
    external_id: Mapped[str] = mapped_column()
    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    condition_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_conditions.id'), nullable=False)
    current_status: Mapped[str] = mapped_column(default='active')

    current_step_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('study_steps.id'), nullable=False)
    current_page_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('step_pages.id'), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    discarded: Mapped[bool] = mapped_column(default=False)

    participant_session: Mapped['ParticipantSession'] = relationship(
        'ParticipantSession', back_populates='participant', cascade='all, delete-orphan'
    )


class Demographic(Base):
    __tablename__ = 'demographics'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_participants.id'))
    age_range: Mapped[str] = mapped_column()
    gender: Mapped[str] = mapped_column()
    gender_other: Mapped[Optional[str]] = mapped_column()
    race: Mapped[str] = mapped_column()
    race_other: Mapped[Optional[str]] = mapped_column()
    education: Mapped[str] = mapped_column()
    country: Mapped[str] = mapped_column()
    state_region: Mapped[Optional[str]] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    version: Mapped[int] = mapped_column()

    discarded: Mapped[bool] = mapped_column(default=False)


class ParticipantSession(Base):
    __tablename__ = 'participant_sessions'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_participants.id'))
    resume_code: Mapped[str] = mapped_column()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    participant: Mapped['StudyParticipant'] = relationship('StudyParticipant', back_populates='participant_session')
