import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import RSSADBBase as Base
from data.models.survey_constructs import ScaleLevel


class Feedback(Base):
	__tablename__ = 'feedback'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False
	)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
	study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study.id'), nullable=False)
	feedback_text: Mapped[str] = mapped_column()
	feedback_type: Mapped[str] = mapped_column()
	feedback_category: Mapped[str] = mapped_column()

	def __init__(
		self,
		participant_id: uuid.UUID,
		study_id: uuid.UUID,
		feedback_text: str,
		feedback_type: str,
		feedback_category: str,
	):
		self.participant_id = participant_id
		self.study_id = study_id
		self.feedback_text = feedback_text
		self.feedback_type = feedback_type
		self.feedback_category = feedback_category


class SurveyItemResponse(Base):
	"""
	Stores participant responses to specific, structured survey items.
	Replaces ParticipantSurveyResponse.
	"""

	__tablename__ = 'survey_item_response'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False
	)
	construct_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('survey_construct.id'), nullable=False
	)
	item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('construct_item.id'), nullable=True)

	# FIXME: response should be non null but for now it is nullable because of older data and a lack of default
	response: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('scale_level.id'))
	scale_level: Mapped[Optional['ScaleLevel']] = relationship()

	date_created: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	date_modified: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	discarded: Mapped[bool] = mapped_column(default=False)

	# Relationships (if needed)
	# participant: Mapped['StudyParticipant'] = relationship('StudyParticipant', back_populates='survey_item_responses')
	# step: Mapped['StudyStep'] = relationship('StudyStep', back_populates='item_responses')
	# construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='item_responses')
	# item: Mapped['ConstructItem'] = relationship('ConstructItem', back_populates='responses')

	def __init__(self, participant_id: uuid.UUID, construct_id: uuid.UUID, item_id: uuid.UUID, response: uuid.UUID):
		self.participant_id = participant_id
		self.construct_id = construct_id
		self.response = response
		self.item_id = item_id


class SurveyFreeformResponse(Base):
	"""
	Stores participant's freeform text responses or comments provided
	within the context of a survey, step, or specific item (if applicable).
	This handles cases where construct_id/item_id might be null.
	"""

	__tablename__ = 'freeform_response'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	participant_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('study_participant.id'), nullable=False
	)
	step_id: Mapped[Optional[uuid.UUID]] = mapped_column(
		UUID(as_uuid=True), ForeignKey('study_step.id'), nullable=True
	)  # Nullable if comment is for entire survey
	item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
		UUID(as_uuid=True), ForeignKey('construct_item.id'), nullable=True
	)  # Nullable if not tied to specific item
	context_tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
	response_text: Mapped[str] = mapped_column()
	date_created: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	date_modified: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		nullable=False,
		default=lambda: datetime.now(timezone.utc),
		onupdate=lambda: datetime.now(timezone.utc),
	)
	discarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

	# Relationships (if needed)
	# participant: Mapped['StudyParticipant'] = relationship('StudyParticipant', back_populates='survey_freeform_responses')
	# step: Mapped['StudyStep'] = relationship('StudyStep', back_populates='freeform_responses')
	# item: Mapped['ConstructItem'] = relationship('ConstructItem', back_populates='freeform_responses')

	def __init__(
		self,
		participant_id: uuid.UUID,
		survey_id: uuid.UUID,
		response_text: str,
		step_id: Optional[uuid.UUID],
		item_id: Optional[uuid.UUID],
		context_tag: Optional[str],
	):
		self.participant_id = participant_id
		self.survey_id = survey_id
		self.response_text = response_text
		self.step_id = step_id
		self.item_id = item_id
		self.context_tag = context_tag
