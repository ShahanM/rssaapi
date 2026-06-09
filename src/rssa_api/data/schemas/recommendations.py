"""Schemas for recommendations."""

import uuid
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar('T')
U = TypeVar('U')


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


class EnrichedAdvisorRecItem(BaseModel, Generic[T, U]):
    """Schema for an enriched advisor recommendation item."""

    id: int
    recommendation: T
    avatar: Avatar | None
    profile_top_n: list[U]


class CommunityScoreRecItem(BaseModel):
    """Schema for community score recommendation item."""

    item: str | int
    community_score: float
    score: float
    community_label: int
    label: int
    cluster: int = 0


class EnrichedCommunityScoreItem(BaseModel, Generic[T]):
    """Schema for enriched community score recommendation item."""

    item: T
    community_score: float
    score: float
    community_label: int
    label: int
    cluster: int = 0


class StandardResponse(BaseModel):
    response_type: Literal['standard']
    items: list[int | str]


class AdvisorResponse(BaseModel):
    response_type: Literal['community_advisors']
    items: list[AdvisorRecItem]


class ComparisonResponse(BaseModel):
    response_type: Literal['community_comparison']
    items: list[CommunityScoreRecItem]


ResponseWrapper = Annotated[
    StandardResponse | AdvisorResponse | ComparisonResponse, Field(discriminator='response_type')
]


class StandardEnrichedResponse(BaseModel, Generic[T]):
    response_type: Literal['standard']
    items: list[T]


class AdvisorEnrichedResponse(BaseModel, Generic[T, U]):
    response_type: Literal['community_advisors']
    items: list[EnrichedAdvisorRecItem[T, U]]


class ComparisonEnrichedResponse(BaseModel, Generic[T]):
    response_type: Literal['community_comparison']
    items: list[EnrichedCommunityScoreItem[T]]


EnrichedResponseWrapper = Annotated[
    StandardEnrichedResponse[T] | AdvisorEnrichedResponse[T, U] | ComparisonEnrichedResponse[T],
    Field(discriminator='response_type'),
]


class TuningPayload(BaseModel):
    sliders: dict[str, float] = Field(default_factory=dict)
    filters: dict[str, list[str]] = Field(default_factory=dict)


class RecommendationContextBase(BaseModel):
    step_id: uuid.UUID
    context_tag: str
    step_page_id: uuid.UUID | None = None

    model_config = ConfigDict(extra='allow')


class StandardRecContext(RecommendationContextBase):
    schema_type: Literal['standard', 'standard_emotion', 'community_comparison', 'community_advisors']


class EmotionRecContext(RecommendationContextBase):
    schema_type: Literal['standard_emotion']
    emotion_input: dict[str, float | str] = Field(..., description='Map of emotion keys to intensity values.')


RecommendationRequestPayload = Annotated[StandardRecContext | EmotionRecContext, Field(discriminator='schema_type')]
