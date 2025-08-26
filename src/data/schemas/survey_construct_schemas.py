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

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class ConstructItemSchema(BaseDBSchema):
	text: str
	order_position: int
	enabled: bool

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class ConstructItemCreateSchema(BaseModel):
	construct_id: uuid.UUID
	text: str


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
			datetime: lambda v: v.isoformat(),
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


class ConstructDetailSchema(BaseDBSchema):
	id: uuid.UUID
	name: str
	desc: str
	items: List[ConstructItemSchema] = Field(validation_alias=AliasPath('items'))
