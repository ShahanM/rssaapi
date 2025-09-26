import uuid

from pydantic import BaseModel

from data.schemas.base_schemas import BaseDBMixin


class SurveyItemResponseBaseSchema(BaseModel):
    construct_id: uuid.UUID
    item_id: uuid.UUID
    scale_id: uuid.UUID
    scale_level_id: uuid.UUID


class TextResponseBaseSchema(BaseModel):
    context_tag: str
    response_text: str


class TextResponseCreateSchema(BaseModel):
    step_id: uuid.UUID
    responses: list[TextResponseBaseSchema]


class TextResponseSchema(TextResponseBaseSchema, BaseDBMixin):
    pass


class RatedItemBaseSchema(BaseModel):
    item_id: uuid.UUID
    rating: int

    def __hash__(self):
        return self.model_dump_json().__hash__()


class RatedItemSchema(RatedItemBaseSchema, BaseDBMixin):
    def __hash__(self):
        return self.model_dump_json().__hash__()


class MovieLensRatingSchema(BaseModel):
    item_id: str
    rating: int
