import uuid
from typing import List, Optional

from pydantic import AliasPath, BaseModel, Field

from data.schemas.base_schemas import BaseDBSchema


class ScaleLevelSchema(BaseDBSchema):
	level: int
	label: str
	enabled: bool


class ConstructItemSchema(BaseDBSchema):
	text: str
	order_position: int
	enabled: bool


class ConstructItemCreateSchema(BaseModel):
	construct_id: uuid.UUID
	text: str
	order_position: int
	item_type: uuid.UUID


class SurveyConstructSchema(BaseDBSchema):
	name: str
	desc: str


class ConstructLinkSchema(BaseModel):
	construct_id: uuid.UUID
	page_id: uuid.UUID
	order_position: int


class LinkedContentSchema(BaseDBSchema):
	content_id: uuid.UUID
	page_id: uuid.UUID
	order_position: int


class ConstructSummarySchema(BaseDBSchema):
	name: str
	desc: str

	construct_type: Optional[str] = Field(validation_alias=AliasPath('construct_type', 'type'))
	scale_name: Optional[str] = Field(validation_alias=AliasPath('construct_scale', 'name'))


class ConstructDetailSchema(BaseDBSchema):
	id: uuid.UUID

	name: str
	desc: str
	scale_name: str = Field(validation_alias=AliasPath('construct_scale', 'name'))
	scale_level_cnt: int = Field(validation_alias=AliasPath('construct_scale', 'levels'))
	scale_levels: List[ScaleLevelSchema] = Field(validation_alias=AliasPath('construct_scale', 'scale_levels'))
	items: List[ConstructItemSchema] = Field(validation_alias=AliasPath('items'))
