import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.base import RSSADBBase as Base
from rssa_api.data.models.rssa_base_models import DBBaseModel


class ConstructItem(DBBaseModel):
    __tablename__ = 'construct_items'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    text: Mapped[str] = mapped_column(nullable=False)  # Also used as its display_name
    notes: Mapped[Optional[str]] = mapped_column()
    order_position: Mapped[int] = mapped_column(nullable=False)

    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))
    construct_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_constructs.id'), nullable=False)

    survey_construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='items')


class SurveyConstruct(DBBaseModel):
    __tablename__ = 'survey_constructs'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

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


class ConstructScale(DBBaseModel):
    __tablename__ = 'construct_scales'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()

    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

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


class ScaleLevel(DBBaseModel):
    __tablename__ = 'scale_levels'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    label: Mapped[str] = mapped_column(nullable=False)
    notes: Mapped[Optional[str]] = mapped_column()
    value: Mapped[int] = mapped_column(nullable=False)

    order_position: Mapped[int] = mapped_column(nullable=False)

    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))
    scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('construct_scales.id'), nullable=False)

    scale: Mapped['ConstructScale'] = relationship('ConstructScale', back_populates='scale_levels')
