"""SQLAlchemy models for survey constructs and related entities."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.models.rssa_base_models import BaseModelMixin, DBBaseModel, DBBaseOrderedModel


class SurveyItem(DBBaseOrderedModel, BaseModelMixin):
    """SQLAlchemy model for the 'construct_items' table.

    Attributes:
        enabled: Indicates if the item is enabled.
        deleted_at: Timestamp of deletion.
        text: The text of the construct item.
        notes: Additional notes about the item.
        order_position: Position of the item in an ordered list.
        created_by_id: Foreign key to the user who created the item.
        construct_id: Foreign key to the associated survey construct.
    """

    __tablename__ = 'survey_items'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    text: Mapped[str] = mapped_column(nullable=False)  # Also used as its display_name
    notes: Mapped[Optional[str]] = mapped_column()
    order_position: Mapped[int] = mapped_column(nullable=False)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))
    survey_construct_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_constructs.id'), nullable=False)

    survey_construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='survey_items')


class SurveyConstruct(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'survey_constructs' table.

    Attributes:
        deleted_at: Timestamp of deletion.
        name: Name of the survey construct.
        description: Description of the survey construct.
        created_by_id: Foreign key to the user who created the construct
    """

    __tablename__ = 'survey_constructs'

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))

    survey_items: Mapped[list[SurveyItem]] = relationship(
        'SurveyItem',
        back_populates='survey_construct',
        uselist=True,
        cascade='all, delete-orphan',
    )
    study_step_page_contents: Mapped[list['StudyStepPageContent']] = relationship(  # type: ignore # noqa: F821
        'StudyStepPageContent', back_populates='survey_construct', uselist=True
    )


class SurveyScale(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'construct_scales' table.

    Attributes:
        enabled: Indicates if the survey scale is enabled.
        deleted_at (Optional[datetime]): Timestamp of deletion.
        name: Name of the survey survey scale.
        description (Optional[str]): Description of the survey scale.
        created_by_id (Optional[uuid.UUID]): Foreign key to the user who created the scale.
    """

    __tablename__ = 'survey_scales'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))

    survey_scale_levels: Mapped[list['SurveyScaleLevel']] = relationship(
        'SurveyScaleLevel',
        back_populates='survey_scale',
        order_by='SurveyScaleLevel.order_position',
        collection_class=ordering_list('order_position'),
        uselist=True,
        cascade='all, delete-orphan',
    )
    study_step_page_contents: Mapped[list['StudyStepPageContent']] = relationship(  # type: ignore # noqa: F821
        'StudyStepPageContent', back_populates='survey_scale', uselist=True
    )


class SurveyScaleLevel(DBBaseOrderedModel, BaseModelMixin):
    """SQLAlchemy model for the 'survey_scale_levels' table.

    Attributes:
        enabled: Indicates if the survey scale level is enabled.
        deleted_at: Timestamp of deletion.
        label: Label of the survey scale level.
        notes: Additional notes about the survey_scale level.
        value: Numeric value of the survey scale level.
        order_position: Position of the survey scale level in an ordered list.
        created_by_id: Foreign key to the user who created the survey scale level.
        scale_id: Foreign key to the associated survey scale.
    """

    __tablename__ = 'survey_scale_levels'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    label: Mapped[str] = mapped_column(nullable=False)
    notes: Mapped[Optional[str]] = mapped_column()
    value: Mapped[int] = mapped_column(nullable=False)

    order_position: Mapped[int] = mapped_column(nullable=False)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))
    survey_scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_scales.id'), nullable=False)

    survey_scale: Mapped['SurveyScale'] = relationship('SurveyScale', back_populates='survey_scale_levels')
