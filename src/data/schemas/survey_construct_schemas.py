import uuid

from pydantic import BaseModel

from data.schemas.base_schemas import BaseDBSchema


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
