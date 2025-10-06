import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# from data.base import RSSADBBase as Base


class DBBaseModel(DeclarativeBase):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class OrderedModelMixing:
    __abstract__ = True
    order_position: Mapped[int] = mapped_column(nullable=False, index=True)


class DBBaseOrderedModel(DBBaseModel, OrderedModelMixing):
    __abstract__ = True
    pass


class BaseModelMixin:
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class StudyParticipantContextMixin:
    __abstract__ = True
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('studies.id'), nullable=False)
    step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('study_steps.id'),
        nullable=False,
        comment='The required step where the context was recorded.',
    )
    step_page_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('step_pages.id'),
        nullable=True,
        comment='The specific page where the recommendation list was displayed (optional).',
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('study_participants.id'), nullable=False
    )
    context_tag: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(default=1)
    discarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class DBBaseParticipantResponseModel(DBBaseModel, StudyParticipantContextMixin):
    __abstract__ = True
    pass
