"""Schemas for recommendations."""

from typing import Literal

from pydantic import BaseModel, Field

from rssa_api.data.schemas.movie_schemas import MovieDetailSchema, MovieSchema


class Avatar(BaseModel):
    """Schema for an avatar."""

    name: str
    alt: str
    src: str


class AdvisorRecItem(BaseModel):
    """Schema for an advisor recommendation item."""

    id: int
    recommendation: int | str
    profile_top_n: list[int | str]


class EnrichedAdvisorRecItem(BaseModel):
    """Schema for an enriched advisor recommendation item."""

    id: int
    recommendation: MovieDetailSchema
    avatar: Avatar | None
    profile_top_n: list[MovieSchema]


class CommunityScoreRecItem(BaseModel):
    """Schema for community score recommendation item."""

    item: str | int
    community_score: float
    score: float
    community_label: int
    label: int
    cluster: int = 0


class EnrichedCommunityScoreItem(BaseModel):
    """Schema for enriched community score recommendation item."""

    item: MovieSchema
    community_score: float
    score: float
    community_label: int
    label: int
    cluster: int = 0


RecUnionType = AdvisorRecItem | CommunityScoreRecItem | int | str


class ResponseWrapper(BaseModel):
    """Wrapper for raw recommendation responses from the algorithm."""

    response_type: Literal['standard', 'community_advisors', 'community_comparison']
    items: list[RecUnionType]


EnrichedRecUnionType = (
    dict[int, EnrichedAdvisorRecItem | EnrichedCommunityScoreItem | MovieDetailSchema] | list[MovieDetailSchema]
)


class EnrichedResponseWrapper(BaseModel):
    """Wrapper for enriched recommendation responses sent to the frontend."""

    # Renamed from 'rec_type' to 'response_type' for consistency!
    response_type: Literal['standard', 'community_advisors', 'community_comparison']
    items: EnrichedRecUnionType


class TuningPayload(BaseModel):
    """Payload for tuning recommendations."""

    sliders: dict[str, float] = Field(default_factory=dict)
    filters: dict[str, list[str]] = Field(default_factory=dict)
