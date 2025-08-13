import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import AliasPath, Field

from data.schemas.base_schemas import BaseDBSchema
from data.schemas.survey_construct_schemas import ConstructItemSchema, ScaleLevelSchema


class PageContentSchema(BaseDBSchema):
	id: uuid.UUID = Field(alias='content_id')  # Same as construct.id
	order_position: int
	enabled: bool

	name: str = Field(validation_alias=AliasPath('survey_construct', 'name'))
	desc: str = Field(validation_alias=AliasPath('survey_construct', 'desc'))
	scale_name: str = Field(validation_alias=AliasPath('construct_scale', 'name'))
	# scale_level_cnt: int = Field(validation_alias=AliasPath('survey_construct', 'construct_scale', 'levels'))
	scale_levels: List[ScaleLevelSchema] = Field(validation_alias=AliasPath('construct_scale', 'scale_levels'))
	items: List[ConstructItemSchema] = Field(validation_alias=AliasPath('survey_construct', 'items'))


class SurveyPageSchema(BaseDBSchema):
	id: uuid.UUID
	study_id: uuid.UUID
	step_id: uuid.UUID

	order_position: int
	name: str
	description: Optional[str]
	date_created: datetime
	enabled: bool

	page_contents: List[PageContentSchema]

	last_page: bool = False

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
		}
