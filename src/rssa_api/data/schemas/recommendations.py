from typing import Literal, Union, Optional, Any
from pydantic import BaseModel, Field
import uuid


class StandardRecResponse(BaseModel):
    response_type: Literal['standard'] = 'standard'
    items: list[int]
    total_count: int


class AdvisorRecResponse(StandardRecResponse):
    response_type: Literal['advisor'] = 'advisor'
    recommendation: int

class EnrichedRecResponse(BaseModel):
    response_type: Literal['enriched'] = 'enriched'
    recommendations: list[Any] # Should be list[MovieSchema] but avoiding circular imports if possible, or use ForwardRef
    total_count: int

RecommendationResponse = Union[StandardRecResponse, AdvisorRecResponse, EnrichedRecResponse]

class TuningPayload(BaseModel):
    sliders: dict[str, float] = Field(default_factory=dict)
    filters: dict[str, list[str]] = Field(default_factory=dict)