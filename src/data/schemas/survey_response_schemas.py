import uuid
from typing import List

from pydantic import BaseModel


class SurveyItemResponse(BaseModel):
	item_id: uuid.UUID
	response_id: uuid.UUID


class SurveyConstructResponse(BaseModel):
	content_id: uuid.UUID
	items: List[SurveyItemResponse]


class SurveyReponseCreateSchema(BaseModel):
	participant_id: uuid.UUID
	step_id: uuid.UUID
	page_id: uuid.UUID
	responses: List[SurveyConstructResponse]


class SurveyItemResponseSchema(BaseModel):
	pass
