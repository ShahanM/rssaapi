import uuid
from typing import List

from pydantic import BaseModel


class SurveyItemResponseSchema(BaseModel):
	item_id: uuid.UUID
	response_id: uuid.UUID


class SurveyConstructResponseSchema(BaseModel):
	content_id: uuid.UUID
	items: List[SurveyItemResponseSchema]


class SurveyReponseCreateSchema(BaseModel):
	participant_id: uuid.UUID
	step_id: uuid.UUID
	page_id: uuid.UUID
	responses: List[SurveyConstructResponseSchema]


class FreeFormTextResponse(BaseModel):
	context_tag: str
	response: str


class FreeformTextResponseCreateSchema(BaseModel):
	step_id: uuid.UUID
	participant_id: uuid.UUID
	responses: List[FreeFormTextResponse]
