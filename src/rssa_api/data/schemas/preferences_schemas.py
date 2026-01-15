"""Schemas for preference visualizations and inputs."""

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from rssa_api.data.schemas.base_schemas import DBMixin
from rssa_api.data.schemas.movie_schemas import MovieDetailSchema, MovieSchema
from rssa_api.data.schemas.participant_response_schemas import RatedItem
from rssa_api.data.schemas.recommendations import Avatar
from rssa_api.data.schemas.study_components import StudyConditionRead


class PrefVizItem(BaseModel):
    """Schema for a single item in the preference visualization."""

    id: str
    community_score: float
    score: float
    community_label: int
    label: int
    cluster: int = 0


class PrefVizDemoRequestSchema(BaseModel):
    """Request schema for the preference visualization demo."""

    user_id: int
    user_condition: int
    ratings: list[RatedItem]
    num_rec: int = 10
    algo: str
    randomize: bool
    init_sample_size: int
    min_rating_count: int

    model_config = ConfigDict(from_attributes=True)

    def __hash__(self):
        return self.model_dump_json().__hash__()


class PreferenceRequestSchema(BaseModel):
    """Request schema for obtaining preferences."""

    user_id: uuid.UUID
    user_condition: uuid.UUID
    rec_type: Literal['baseline', 'reference', 'diverse']
    ratings: list[RatedItem]

    def __hash__(self):
        return self.model_dump_json().__hash__()


class PrefVizMetadata(BaseModel, frozen=True):
    """Metadata for the preference visualization response."""

    algo: str
    randomize: bool
    init_sample_size: int
    min_rating_count: int
    num_rec: int


class PrefVizDemoResponseSchema(BaseModel):
    """Response schema for the preference visualization demo."""

    metadata: PrefVizMetadata
    recommendations: list[PrefVizItem]

    model_config = ConfigDict(from_attributes=True)

    def __hash__(self):
        return self.model_dump_json().__hash__()


class PrefVizResponseSchema(BaseModel):
    """Response schema for preference visualization."""

    metadata: PrefVizMetadata
    recommendations: list[PrefVizItem]

    def __hash__(self):
        return self.model_dump_json().__hash__()


class EmotionContinuousInputSchema(BaseModel):
    """Schema for continuous emotion input."""

    emotion: str
    switch: Literal['ignore', 'diverse', 'specified']
    weight: float


class EmotionDiscreteInputSchema(BaseModel):
    """Schema for discrete emotion input."""

    emotion: str
    weight: Literal['low', 'high', 'diverse', 'ignore']


class EmotionInputSchema(BaseModel):
    """Schema for emotion-based recommendation input."""

    user_id: uuid.UUID
    user_condition: uuid.UUID
    input_type: Literal['discrete', 'continuous']
    emotion_input: list[EmotionDiscreteInputSchema] | list[EmotionContinuousInputSchema]
    ratings: list[RatedItem]
    num_rec: int


class RatingSchemaExperimental(BaseModel):
    """Schema for rating-based recommendation input."""

    # TODO: Fix the parameters and make an experimental control endpoint
    user_id: int
    user_condition: int
    ratings: list[RatedItem]
    rec_type: int
    num_rec: int = 10
    low_val: float = 0.3
    high_val: float = 0.8


class EmotionInputSchemaExperimental(BaseModel):
    """Schema for emotion-based recommendation input."""

    # TODO: Fix the parameters and make an experimental control endpoint
    user_id: int
    condition_algo: int
    input_type: Literal['discrete', 'continuous']
    emotion_input: list[EmotionDiscreteInputSchema] | list[EmotionContinuousInputSchema]
    ratings: list[RatedItem]
    num_rec: int
    item_pool_size: int
    scale_vector: bool = False
    low_val: float = 0.3
    high_val: float = 0.8
    algo: str
    dist_method: str
    diversity_criterion: str
    diversity_sample_size: int | None


class RecommendationRequestPayload(BaseModel):
    """Payload for requesting recommendations."""

    step_id: uuid.UUID
    step_page_id: uuid.UUID | None = None
    context_tag: str
    rec_type: Literal['baseline', 'reference', 'diverse']

    ratings: list[RatedItem]


class AdvisorProfileSchema(BaseModel):
    """Schema for an advisor's profile."""

    id: str
    movies: list[MovieSchema]
    recommendation: MovieDetailSchema
    avatar: Avatar | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class RecommendationJsonBaseSchema(BaseModel):
    """Base schema for recommendation JSON storage."""

    condition: StudyConditionRead | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class RecommendationJsonPrefCommSchema(RecommendationJsonBaseSchema):
    """Schema for PrefComm recommendation JSON."""

    advisors: list[AdvisorProfileSchema]


class PreferenceVizRecommendedItemSchema(MovieSchema, PrefVizItem):
    """Schema for a recommended item in preference visualization."""

    pass


class RecommendationJsonPrefVizSchema(RecommendationJsonBaseSchema):
    """Schema for PrefViz recommendation JSON."""

    prefviz_map: dict[str, PreferenceVizRecommendedItemSchema]


class RecommendationContextBaseSchema(BaseModel):
    """Base schema for recommendation context."""

    step_id: uuid.UUID = Field(validation_alias='study_step_id')
    step_page_id: uuid.UUID | None = Field(default=None, validation_alias='study_step_page_id')
    context_tag: str

    recommendations_json: Any


class RecommendationContextSchema(RecommendationContextBaseSchema, DBMixin):
    """Schema for recommendation context with DB mixin."""

    pass
