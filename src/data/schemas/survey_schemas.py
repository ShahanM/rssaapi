import uuid
from datetime import datetime
from typing import Optional

from pydantic import AliasPath, Field

from data.schemas.base_schemas import BaseDBSchema
from data.schemas.survey_construct_schemas import ConstructItemSchema, ScaleLevelSchema


class PageContentSchema(BaseDBSchema):
	order_position: int

	construct_id: uuid.UUID = Field(validation_alias='content_id')
	items: list[ConstructItemSchema] = Field(validation_alias=AliasPath('survey_construct', 'items'))

	name: str = Field(validation_alias=AliasPath('survey_construct', 'name'))
	desc: str = Field(validation_alias=AliasPath('survey_construct', 'desc'))

	scale_id: uuid.UUID = Field(validation_alias=AliasPath('construct_scale', 'id'))
	scale_name: str = Field(validation_alias=AliasPath('construct_scale', 'name'))
	scale_levels: list[ScaleLevelSchema] = Field(validation_alias=AliasPath('construct_scale', 'scale_levels'))

	enabled: bool

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class SurveyPageSchema(BaseDBSchema):
	id: uuid.UUID
	study_id: uuid.UUID
	step_id: uuid.UUID

	order_position: int

	name: str
	title: Optional[str]
	instructions: Optional[str]
	description: Optional[str]
	page_contents: list[PageContentSchema]

	enabled: bool
	date_created: datetime
	last_page: bool = False

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}
