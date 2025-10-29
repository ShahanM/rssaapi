import uuid
from datetime import datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel

from rssa_api.data.schemas.base_schemas import BaseDBMixin
from rssa_api.data.schemas.movie_schemas import MovieDetailSchema, MovieSchema
from rssa_api.data.schemas.participant_response_schemas import RatedItemBaseSchema, RatedItemSchema
from rssa_api.data.schemas.study_components import StudyConditionSchema


class PrefVizItem(BaseModel):
    item_id: str
    community_score: float
    user_score: float
    community_label: int
    user_label: int
    cluster: int = 0


class PrefVizDemoRequestSchema(BaseModel):
    user_id: int
    user_condition: int
    ratings: list[RatedItemSchema]
    num_rec: int = 10
    algo: str
    randomize: bool
    init_sample_size: int
    min_rating_count: int

    class Config:
        from_attributes = True

    def __hash__(self):
        return self.model_dump_json().__hash__()


class PreferenceRequestSchema(BaseModel):
    user_id: uuid.UUID
    user_condition: uuid.UUID
    rec_type: Literal['baseline', 'reference', 'diverse']
    ratings: list[RatedItemSchema]

    def __hash__(self):
        return self.model_dump_json().__hash__()


class PrefVizMetadata(BaseModel, frozen=True):
    algo: str
    randomize: bool
    init_sample_size: int
    min_rating_count: int
    num_rec: int


class PrefVizDemoResponseSchema(BaseModel):
    metadata: PrefVizMetadata
    recommendations: list[PrefVizItem]

    class Config:
        from_attributes = True

    def __hash__(self):
        return self.model_dump_json().__hash__()


class PrefVizResponseSchema(BaseModel):
    metadata: PrefVizMetadata
    recommendations: list[PrefVizItem]

    def __hash__(self):
        return self.model_dump_json().__hash__()


class EmotionContinuousInputSchema(BaseModel):
    emotion: str
    switch: Literal['ignore', 'diverse', 'specified']
    weight: float


class EmotionDiscreteInputSchema(BaseModel):
    emotion: str
    weight: Literal['low', 'high', 'diverse', 'ignore']


class EmotionInputSchema(BaseModel):
    user_id: uuid.UUID
    user_condition: uuid.UUID
    input_type: Literal['discrete', 'continuous']
    emotion_input: Union[list[EmotionDiscreteInputSchema], list[EmotionContinuousInputSchema]]
    ratings: list[RatedItemSchema]
    num_rec: int


class RatingSchemaExperimental(BaseModel):
    user_id: int
    user_condition: int
    ratings: list[RatedItemSchema]
    rec_type: int
    num_rec: int = 10
    low_val: float = 0.3
    high_val: float = 0.8


class EmotionInputSchemaExperimental(BaseModel):
    user_id: int
    condition_algo: int
    input_type: Literal['discrete', 'continuous']
    emotion_input: Union[list[EmotionDiscreteInputSchema], list[EmotionContinuousInputSchema]]
    ratings: list[RatedItemSchema]
    num_rec: int
    item_pool_size: int
    scale_vector: bool = False
    low_val: float = 0.3
    high_val: float = 0.8
    algo: str
    dist_method: str
    diversity_criterion: str
    diversity_sample_size: Optional[int]


class RecommendationRequestPayload(BaseModel):
    step_id: uuid.UUID
    step_page_id: Optional[uuid.UUID] = None
    context_tag: str
    rec_type: Literal['baseline', 'reference', 'diverse']

    ratings: list[RatedItemBaseSchema]


class Avatar(BaseModel):
    name: str
    alt: str
    src: str


class AdvisorProfileSchema(BaseModel):
    id: str
    movies: list[MovieSchema]
    recommendation: MovieDetailSchema
    avatar: Optional[Avatar]

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }


class RecommendationJsonBaseSchema(BaseModel):
    condition: Optional[StudyConditionSchema] = None

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }


class RecommendationJsonPrefCommSchema(RecommendationJsonBaseSchema):
    advisors: list[AdvisorProfileSchema]


class PreferenceVizRecommendedItemSchema(MovieSchema, PrefVizItem):
    pass


class RecommendationJsonPrefVizSchema(RecommendationJsonBaseSchema):
    prefviz_map: dict[str, PreferenceVizRecommendedItemSchema]


class RecommendationContextBaseSchema(BaseModel):
    step_id: uuid.UUID
    step_page_id: Optional[uuid.UUID] = None
    context_tag: str

    recommendations_json: Any


class RecommendationContextSchema(RecommendationContextBaseSchema, BaseDBMixin):
    pass
