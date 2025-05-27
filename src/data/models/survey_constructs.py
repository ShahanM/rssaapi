import uuid
from typing import Union

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import RSSADBBase as Base


class ConstructItemType(Base):
	__tablename__ = 'construct_item_type'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type: Mapped[str] = mapped_column(String, nullable=False)

	def __init__(self, type: str):
		self.type = type


class ConstructType(Base):
	__tablename__ = 'construct_type'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type: Mapped[str] = mapped_column()
	enabled: Mapped[bool] = mapped_column(default=True)

	def __init__(self, type: str):
		self.type = type


class SurveyConstruct(Base):
	__tablename__ = 'survey_construct'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	name = Column(String, nullable=False)
	desc = Column(String, nullable=False)

	type = Column(UUID(as_uuid=True), ForeignKey('construct_type.id'), nullable=True)
	scale = Column(UUID(as_uuid=True), ForeignKey('construct_scale.id'), nullable=True)

	items = relationship('ConstructItem', back_populates='construct', uselist=True, cascade='all, delete-orphan')

	def __init__(self, name: str, desc: str, type_id: uuid.UUID, scale_id: Union[uuid.UUID, None] = None):
		self.name = name
		self.desc = desc
		self.type = type_id
		self.scale = scale_id


class ConstructItem(Base):
	__tablename__ = 'construct_item'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	construct_id = Column(UUID(as_uuid=True), ForeignKey('survey_construct.id'), nullable=False)
	text = Column(String, nullable=False)
	order_position = Column(Integer, nullable=False)
	item_type = Column(UUID(as_uuid=True), ForeignKey('construct_item_type.id'), nullable=False)
	enabled = Column(Boolean, nullable=False, default=True)

	construct = relationship('SurveyConstruct', back_populates='items')

	def __init__(self, construct_id: uuid.UUID, text: str, order_position: int, item_type: uuid.UUID):
		self.construct_id = construct_id
		self.text = text
		self.order_position = order_position
		self.item_type = item_type


class ConstructScale(Base):
	__tablename__ = 'construct_scale'

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	levels = Column(Integer, nullable=False)
	name = Column(String, nullable=False)
	enabled = Column(Boolean, nullable=False, default=True)

	scale_levels = relationship('ScaleLevel', back_populates='scale', uselist=True, cascade='all, delete-orphan')

	def __init__(self, levels: int, name: str):
		self.levels = levels
		self.name = name


class ScaleLevel(Base):
	__tablename__ = 'scale_level'

	level = Column(Integer, primary_key=True)
	label = Column(String, nullable=False)
	scale_id = Column(UUID(as_uuid=True), ForeignKey('construct_scale.id'), nullable=False)
	enabled = Column(Boolean, nullable=False, default=True)

	scale = relationship('ConstructScale', back_populates='scale_levels')

	def __init__(self, level: int, label: str, scale_id: uuid.UUID):
		self.level = level
		self.label = label
		self.scale_id = scale_id
