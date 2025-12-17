import uuid
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field

from rssa_api.data.schemas.movie_schemas import MovieDetailSchema, MovieSchema


class Avatar(BaseModel):
    name: str
    alt: str
    src: str


class StandardRecResponse(BaseModel):
    response_type: Literal['standard'] = 'standard'
    items: list[int]
    total_count: int


class AdvisorRecItem(BaseModel):
    id: int
    recommendation: Union[int, str]
    profile_top_n: list[Union[int, str]]


class EnrichedAdvisorRecItem(BaseModel):
    id: int
    recommendation: MovieDetailSchema
    avatar: Optional[Avatar]
    profile_top_n: list[MovieSchema]


class EnrichedRecResponse(BaseModel):
    # response_type: Literal['enriched'] = 'enriched'
    items: list[MovieDetailSchema]
    # total_count: int


class CommunityScoreRecItem(BaseModel):
    item: Union[str, int]
    community_score: float
    score: float
    community_label: int
    label: int
    cluster: int = 0


class EnrichedCommunityScoreItem(BaseModel):
    item: MovieSchema
    community_score: float
    score: float
    community_label: int
    label: int
    cluster: int = 0


RecUnionType = Union[AdvisorRecItem, CommunityScoreRecItem, int, str]


class ResponseWrapper(BaseModel):
    response_type: Literal['standard', 'community_advisors', 'community_comparison']
    items: list[RecUnionType]
    # total_count: int # FIXME: We eventually want this but it is not very important right now.


# class EnrichedResponseWrapper(BaseModel):


# RecommendationResponse = Union[StandardRecResponse, EnrichedRecResponse]

RecommendationResponse = Union[
    dict[int, Union[EnrichedAdvisorRecItem, EnrichedCommunityScoreItem]], list[MovieDetailSchema]
]


class TuningPayload(BaseModel):
    sliders: dict[str, float] = Field(default_factory=dict)
    filters: dict[str, list[str]] = Field(default_factory=dict)
