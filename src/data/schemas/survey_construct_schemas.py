import datetime
import uuid
from typing import List, Optional

from pydantic import AliasPath, BaseModel, Field

from data.schemas.base_schemas import BaseDBSchema


class ScaleLevelCreateSchema(BaseModel):
	scale_id: uuid.UUID
	value: int
	label: str


class ScaleLevelSchema(BaseDBSchema):
	order_position: int
	value: int
	label: str
	enabled: bool


class ConstructItemSchema(BaseDBSchema):
	text: str
	order_position: int
	enabled: bool


class ConstructItemCreateSchema(BaseModel):
	construct_id: uuid.UUID
	text: str
	# order_position: int
	# item_type: uuid.UUID


# class ConstructTypeSchema(BaseModel):
# 	id: uuid.UUID
# 	type: str

# 	enabled: bool


# 	class Config:
# 		from_attributes = True
# 		json_encoders = {
# 			uuid.UUID: lambda v: str(v),
# 		}
class ConstructScaleCreateSchema(BaseModel):
	name: Optional[str] = None
	description: Optional[str] = None


class ConstructScaleSchema(BaseDBSchema):
	id: uuid.UUID
	name: str
	description: Optional[str] = None
	created_by: Optional[str] = None

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
		}


class ConstructScaleSummarySchema(BaseDBSchema):
	id: uuid.UUID
	name: str
	description: Optional[str] = None
	created_by: Optional[str] = None
	date_created: datetime.datetime

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class ConstructScaleDetailSchema(BaseDBSchema):
	id: uuid.UUID
	name: str
	description: Optional[str] = None
	created_by: Optional[str] = None
	date_created: datetime.datetime
	scale_levels: List[ScaleLevelSchema] = Field(validation_alias=AliasPath('scale_levels'))

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class SurveyConstructCreateSchema(BaseModel):
	name: str
	desc: str


class SurveyConstructSchema(BaseDBSchema):
	id: uuid.UUID
	name: str
	desc: str

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
		}


class ConstructLinkSchema(BaseModel):
	construct_id: uuid.UUID
	page_id: uuid.UUID
	order_position: int


class PageContentCreateSchema(BaseModel):
	page_id: uuid.UUID
	construct_id: uuid.UUID
	scale_id: uuid.UUID


# class ConstructSummarySchema(BaseDBSchema):
# name: str
# desc: str

# construct_type: Optional[str] = Field(validation_alias=AliasPath('construct_type', 'type'))
# scale_name: Optional[str] = Field(validation_alias=AliasPath('construct_scale', 'name'))


class ConstructDetailSchema(BaseDBSchema):
	id: uuid.UUID

	name: str
	desc: str
	# scale_name: str = Field(validation_alias=AliasPath('construct_scale', 'name'))
	# scale_level_cnt: int = Field(validation_alias=AliasPath('construct_scale', 'levels'))
	# scale_levels: List[ScaleLevelSchema] = Field(validation_alias=AliasPath('construct_scale', 'scale_levels'))
	items: List[ConstructItemSchema] = Field(validation_alias=AliasPath('items'))


class ReorderPayloadSchema(BaseModel):
	id: uuid.UUID
	order_position: int
