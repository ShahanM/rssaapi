import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from rssa_api.data.models.rssa_base_models import BaseModelMixin, DBBaseModel, StudyParticipantContextMixin


# class ParticipantRating(BaseModelMixin, StudyParticipantContextMixin, DBBaseModel):
#     """
#     Stores participant ratings for various content within the study.
#     """

#     __tablename__ = 'participant_ratings'

#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

#     participant_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), ForeignKey('study_participants.id'), nullable=False
#     )

#     item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
#     item_table_name: Mapped[str] = mapped_column()
#     rating: Mapped[int] = mapped_column()
#     scale_min: Mapped[int] = mapped_column()
#     scale_max: Mapped[int] = mapped_column()
#     created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
#     updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

#     version: Mapped[int] = mapped_column()


# class ParticipantInteractionLog(BaseModelMixin, StudyParticipantContextMixin, DBBaseModel):
#     """
#     Stores general participant interaction events/behaviors within the study.
#     """

#     __tablename__ = 'participant_interaction_logs'

#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     participant_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), ForeignKey('study_participants.id'), nullable=False
#     )
#     action: Mapped[str] = mapped_column()
#     action_data: Mapped[str] = mapped_column()
#     date_created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))
