import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data.base import RSSADBBase as Base


class ContentRating(Base):
	"""
	Stores participant ratings for various content within the study.
	"""

	__tablename__ = 'content_rating'

	participant_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False
	)
	content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
	content_type: Mapped[str] = mapped_column()
	rating: Mapped[int] = mapped_column()
	scale_min: Mapped[int] = mapped_column()
	scale_max: Mapped[int] = mapped_column()
	date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

	PrimaryKeyConstraint(participant_id, content_type, content_id)

	def __init__(
		self,
		participant_id: uuid.UUID,
		content_type: str,
		content_id: uuid.UUID,
		rating: int,
		scale_min: int,
		scale_max: int,
	):
		self.participant_id = participant_id
		self.content_type = content_type
		self.content_id = content_id
		self.rating = rating
		self.scale_min = scale_min
		self.scale_max = scale_max


class InteractionLog(Base):
	"""
	Stores general participant interaction events/behaviors within the study.
	"""

	__tablename__ = 'interaction_log'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False
	)
	action: Mapped[str] = mapped_column()
	action_data: Mapped[str] = mapped_column()
	date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))

	def __init__(self, participant_id: uuid.UUID, action: str, action_data: str):
		self.participant_id = participant_id
		self.action = action
		self.action_data = action_data
