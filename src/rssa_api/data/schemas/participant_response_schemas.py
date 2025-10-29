import uuid
from typing import Any, Optional

from pydantic import BaseModel

from rssa_api.data.schemas.base_schemas import BaseDBMixin, VersionMixin


class ParticipantResponseContextMixin:
    __abstract__ = True
    step_id: uuid.UUID
    step_page_id: Optional[uuid.UUID] = None
    context_tag: str


class SurveyItemResponseBaseSchema(BaseModel, ParticipantResponseContextMixin):
    construct_id: uuid.UUID
    item_id: uuid.UUID
    scale_id: uuid.UUID
    scale_level_id: uuid.UUID


class SurveyItemResponseSchema(SurveyItemResponseBaseSchema, VersionMixin, BaseDBMixin):
    pass


class SurveyItemResponseUpdatePayload(BaseDBMixin, VersionMixin):
    scale_level_id: uuid.UUID


class TextResponseBaseSchema(BaseModel, ParticipantResponseContextMixin):
    response_text: str


class TextResponseCreateSchema(BaseModel):
    step_id: uuid.UUID
    responses: list[TextResponseBaseSchema]


class TextResponseSchema(TextResponseBaseSchema, BaseDBMixin):
    pass


class RatedItemBaseSchema(BaseModel):
    item_id: uuid.UUID
    rating: int


class RatedItemSchema(RatedItemBaseSchema, VersionMixin, BaseDBMixin):
    pass


class ParticipantContentRatingPayload(BaseModel, ParticipantResponseContextMixin):
    rated_item: RatedItemBaseSchema


class MovieLensRatingSchema(BaseModel):
    item_id: str
    rating: int


class DynamicPaylaodSchema(BaseModel):
    experimnet_condition: Optional[str] = None
    extra: dict[str, Any] = {}

    model_config = {'extra': 'allow'}


class StudyInteractionResponseBaseSchema(BaseModel, ParticipantResponseContextMixin):
    payload_json: DynamicPaylaodSchema


class StudyInteractionResponseSchema(VersionMixin, BaseDBMixin):
    payload_json: DynamicPaylaodSchema
