"""SQLAlchemy models for survey constructs and related entities."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.models.rssa_base_models import BaseModelMixin, DBBaseModel


class ConstructItem(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'construct_items' table.

    Attributes:
        enabled (bool): Indicates if the item is enabled.
        deleted_at (Optional[datetime]): Timestamp of deletion.
        text (str): The text of the construct item.
        notes (Optional[str]): Additional notes about the item.
        order_position (int): Position of the item in an ordered list.
        created_by_id (Optional[uuid.UUID]): Foreign key to the user who created the item.
        construct_id (uuid.UUID): Foreign key to the associated survey construct.
    """

    __tablename__ = 'construct_items'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    text: Mapped[str] = mapped_column(nullable=False)  # Also used as its display_name
    notes: Mapped[Optional[str]] = mapped_column()
    order_position: Mapped[int] = mapped_column(nullable=False)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))
    construct_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_constructs.id'), nullable=False)

    survey_construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='items')


class SurveyConstruct(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'survey_constructs' table.

    Attributes:
        deleted_at (Optional[datetime]): Timestamp of deletion.
        name (str): Name of the survey construct.
        description (str): Description of the survey construct.
        created_by_id (Optional[uuid.UUID]): Foreign key to the user who created the construct
    """

    __tablename__ = 'survey_constructs'

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))

    items: Mapped[list[ConstructItem]] = relationship(
        'ConstructItem',
        back_populates='survey_construct',
        uselist=True,
        cascade='all, delete-orphan',
    )
    page_contents: Mapped[list['PageContent']] = relationship(  # type: ignore # noqa: F821
        'PageContent', back_populates='survey_construct', uselist=True
    )


class ConstructScale(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'construct_scales' table.

    Attributes:
        enabled (bool): Indicates if the scale is enabled.
        deleted_at (Optional[datetime]): Timestamp of deletion.
        name (str): Name of the construct scale.
        description (Optional[str]): Description of the construct scale.
        created_by_id (Optional[uuid.UUID]): Foreign key to the user who created the scale.
    """

    __tablename__ = 'construct_scales'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))

    scale_levels: Mapped[list['ScaleLevel']] = relationship(
        'ScaleLevel',
        back_populates='scale',
        order_by='ScaleLevel.order_position',
        collection_class=ordering_list('order_position'),
        uselist=True,
        cascade='all, delete-orphan',
    )
    page_contents: Mapped[list['PageContent']] = relationship(  # type: ignore # noqa: F821
        'PageContent', back_populates='construct_scale', uselist=True
    )


class ScaleLevel(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'scale_levels' table.

    Attributes:
        enabled (bool): Indicates if the scale level is enabled.
        deleted_at (Optional[datetime]): Timestamp of deletion.
        label (str): Label of the scale level.
        notes (Optional[str]): Additional notes about the scale level.
        value (int): Numeric value of the scale level.
        order_position (int): Position of the scale level in an ordered list.
        created_by_id (Optional[uuid.UUID]): Foreign key to the user who created the scale level.
        scale_id (uuid.UUID): Foreign key to the associated construct scale.
    """

    __tablename__ = 'scale_levels'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    label: Mapped[str] = mapped_column(nullable=False)
    notes: Mapped[Optional[str]] = mapped_column()
    value: Mapped[int] = mapped_column(nullable=False)

    order_position: Mapped[int] = mapped_column(nullable=False)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))
    scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('construct_scales.id'), nullable=False)

    scale: Mapped['ConstructScale'] = relationship('ConstructScale', back_populates='scale_levels')
