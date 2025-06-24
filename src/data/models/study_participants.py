import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data.base import RSSADBBase as Base


class ParticipantType(Base):
	__tablename__ = 'participant_type'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type: Mapped[str] = mapped_column()

	def __init__(self, type: str):
		self.type = type


class StudyParticipant(Base):
	__tablename__ = 'study_participant'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_type: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('participant_type.id'), nullable=False
	)
	external_id: Mapped[str] = mapped_column()
	study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)
	condition_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('study_condition.id'), nullable=False
	)
	current_status: Mapped[str] = mapped_column()
	current_step: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_step.id'), nullable=False)
	current_page: Mapped[Optional[uuid.UUID]] = mapped_column(
		UUID(as_uuid=True), ForeignKey('step_page.id'), nullable=True
	)
	date_created: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	date_updated: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	discarded: Mapped[bool] = mapped_column(default=False)

	def __init__(
		self,
		participant_type: uuid.UUID,
		study_id: uuid.UUID,
		condition_id: uuid.UUID,
		external_id: str,
		current_step: uuid.UUID,
		current_page: Optional[uuid.UUID] = None,
	):
		self.participant_type = participant_type
		self.study_id = study_id
		self.condition_id = condition_id
		self.current_status = 'active'
		self.external_id = external_id
		self.current_step = current_step
		self.current_page = current_page


class Demographic(Base):
	__tablename__ = 'demographics'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_participant.id'))
	age_range: Mapped[str] = mapped_column()
	gender: Mapped[str] = mapped_column()
	gender_other: Mapped[Optional[str]] = mapped_column()
	race: Mapped[str] = mapped_column()
	race_other: Mapped[Optional[str]] = mapped_column()
	education: Mapped[str] = mapped_column()
	country: Mapped[str] = mapped_column()
	state_region: Mapped[Optional[str]] = mapped_column()
	date_created: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	date_updated: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	discarded: Mapped[bool] = mapped_column(default=False)

	def __init__(
		self,
		participant_id: uuid.UUID,
		age_range: str,
		gender: str,
		race: str,
		education: str,
		country: str,
		state_region: Optional[str],
		gender_other: Optional[str],
		race_other: Optional[str],
	):
		self.participant_id = participant_id
		self.age_range = age_range
		self.gender = gender
		self.gender_other = gender_other
		self.race = race
		self.race_other = race_other
		self.education = education
		self.country = country
		self.state_region = state_region
