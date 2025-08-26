import uuid

from pydantic import BaseModel


class SurveyItemResponseSchema(BaseModel):
	construct_id: uuid.UUID
	item_id: uuid.UUID
	scale_id: uuid.UUID
	scale_level_id: uuid.UUID


class SurveyConstructResponseSchema(BaseModel):
	content_id: uuid.UUID
	items: list[SurveyItemResponseSchema]


class SurveyReponseCreateSchema(BaseModel):
	participant_id: uuid.UUID
	step_id: uuid.UUID
	page_id: uuid.UUID
	responses: list[SurveyItemResponseSchema]


class FreeFormTextResponse(BaseModel):
	context_tag: str
	response: str


class FreeformTextResponseCreateSchema(BaseModel):
	step_id: uuid.UUID
	participant_id: uuid.UUID
	responses: list[FreeFormTextResponse]
