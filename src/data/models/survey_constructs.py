import uuid
from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import RSSADBBase as Base


class ConstructItemType(Base):
	__tablename__ = 'construct_item_type'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type: Mapped[str] = mapped_column(String, nullable=False)

	# def __init__(self, type: str):
	# 	self.type = type


class ConstructType(Base):
	__tablename__ = 'construct_type'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type: Mapped[str] = mapped_column()
	enabled: Mapped[bool] = mapped_column(default=True)

	# def __init__(self, type: str):
	# 	self.type = type


class ConstructItem(Base):
	__tablename__ = 'construct_item'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	construct_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('survey_construct.id'), nullable=False
	)
	text: Mapped[str] = mapped_column()
	order_position: Mapped[int] = mapped_column()

	item_type: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True), ForeignKey('construct_item_type.id'), nullable=False
	)
	enabled: Mapped[bool] = mapped_column(default=True)

	survey_construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='items')
	item_type_obj: Mapped[ConstructItemType] = relationship(ConstructItemType)

	# def __init__(self, construct_id: uuid.UUID, text: str, order_position: int, item_type: uuid.UUID):
	# 	self.construct_id = construct_id
	# 	self.text = text
	# 	self.order_position = order_position
	# 	self.item_type = item_type


class SurveyConstruct(Base):
	__tablename__ = 'survey_construct'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	name: Mapped[str] = mapped_column()
	desc: Mapped[str] = mapped_column()

	type: Mapped[Optional[uuid.UUID]] = mapped_column(
		UUID(as_uuid=True), ForeignKey('construct_type.id'), nullable=True
	)
	scale: Mapped[Optional[uuid.UUID]] = mapped_column(
		UUID(as_uuid=True), ForeignKey('construct_scale.id'), nullable=True
	)

	items: Mapped[list[ConstructItem]] = relationship(
		'ConstructItem', back_populates='survey_construct', uselist=True, cascade='all, delete-orphan'
	)

	construct_type: Mapped[Optional[ConstructType]] = relationship(ConstructType)
	construct_scale: Mapped[Optional['ConstructScale']] = relationship('ConstructScale')

	page_contents: Mapped[list['PageContent']] = relationship(  # type: ignore # noqa: F821
		'PageContent', back_populates='survey_construct', uselist=True
	)

	# def __init__(self, name: str, desc: str, type_id: uuid.UUID, scale_id: Optional[uuid.UUID] = None):
	# 	self.name = name
	# 	self.desc = desc
	# 	self.type = type_id
	# 	self.scale = scale_id


class ConstructScale(Base):
	__tablename__ = 'construct_scale'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	levels = Column(Integer, nullable=False)
	name = Column(String, nullable=False)
	enabled = Column(Boolean, nullable=False, default=True)

	scale_levels = relationship('ScaleLevel', back_populates='scale', uselist=True, cascade='all, delete-orphan')

	# def __init__(self, levels: int, name: str):
	# 	self.levels = levels
	# 	self.name = name


class ScaleLevel(Base):
	__tablename__ = 'scale_level'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	level: Mapped[int] = mapped_column()
	label: Mapped[str] = mapped_column()
	scale_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('construct_scale.id'), nullable=False)
	enabled: Mapped[bool] = mapped_column(default=True)

	scale: Mapped['ConstructScale'] = relationship('ConstructScale', back_populates='scale_levels')

	# def __init__(self, level: int, label: str, scale_id: uuid.UUID):
	# 	self.level = level
	# 	self.label = label
	# 	self.scale_id = scale_id
