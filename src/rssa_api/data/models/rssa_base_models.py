"""SQLAlchemy base models for the RSSA API."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class DBBaseModel(DeclarativeBase):
    """Base class for all database models in the RSSA API.

    Attributes:
        id: Primary key.
    """

    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class OrderedModelMixing:
    """Mixin class to add ordering functionality to models.

    Attributes:
        order_position: Position of the model in an ordered list.
    """

    __abstract__ = True
    order_position: Mapped[int] = mapped_column(nullable=False, index=True)


class DBBaseOrderedModel(DBBaseModel, OrderedModelMixing):
    """Base class for ordered database models in the RSSA API.

    Attributes:
        Inherits id and order_position from parent classes.
    """

    __abstract__ = True
    pass


class BaseModelMixin:
    """Mixin class to add common timestamp fields to models.

    Attributes:
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

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
    """Mixin class to add study participant context fields to models.

    Attributes:
        study_id: Foreign key to the study.
        study_step_id: Foreign key to the study step.
        study_step_page_id (Optional[uuid.UUID]): Foreign key to the step page.
        study_participant_id: Foreign key to the study participant.
        context_tag: Context tag for the response.
        version: Version of the response.
        discarded: Indicates if the response is discarded.
    """

    __abstract__ = True
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('studies.id'), nullable=False)
    study_step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('study_steps.id'),
        nullable=False,
        comment='The required step where the context was recorded.',
    )
    study_step_page_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('study_step_pages.id'),
        nullable=True,
        comment='The specific page where the recommendation list was displayed (optional).',
    )
    study_participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('study_participants.id'), nullable=False
    )
    context_tag: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(default=1)
    discarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class DBBaseParticipantResponseModel(DBBaseModel, StudyParticipantContextMixin):
    """Base class for participant response models in the RSSA API.

    Attributes:
        Inherits id, study participant context fields from parent classes.
    """

    __abstract__ = True
    pass
