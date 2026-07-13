from typing import Annotated, Literal

import structlog
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from rssa_api.data.schemas.participant_response_schemas import MovieLensRating
from rssa_api.data.schemas.recommendations import EnrichedResponseWrapper
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.recommenders.registry import REGISTRY, SCHEMA_REGISTRY
from rssa_api.services.dependencies import RecommenderServiceDep

log = structlog.getLogger(__name__)

router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)


# 1. The New Decoupled Base Schema
class DecoupledRecommendationContextBase(BaseModel):
    context_tag: str
    algorithm_key: str | None = None

    model_config = ConfigDict(extra='allow')


# 2. The Decoupled Context Variants
class DecoupledStandardRecContext(DecoupledRecommendationContextBase):
    schema_type: Literal['standard', 'standard_emotion', 'community_comparison', 'community_advisors']


class DecoupledEmotionRecContext(DecoupledRecommendationContextBase):
    schema_type: Literal['standard_emotion']
    emotion_input: dict[str, float | str] = Field(..., description='Map of emotion keys to intensity values.')


# 3. The New Decoupled Payload Type
DecoupledRecommendationRequestPayload = Annotated[
    DecoupledStandardRecContext | DecoupledEmotionRecContext, Field(discriminator='schema_type')
]


@router.post('/', response_model=EnrichedResponseWrapper)
async def get_recommendations(
    recommender_service: RecommenderServiceDep,
    ratings: list[MovieLensRating],
    limit: int,
    context_data: DecoupledRecommendationRequestPayload = Body(...),
):
    """Get recommendations for the current participant."""
    schema_key = context_data.schema_type  # FIXME: Consider changing the name schema_type to something appropriate
    algorithm_key = context_data.algorithm_key

    print(algorithm_key)
    if algorithm_key not in REGISTRY:
        raise HTTPException(status_code=500, detail='Assigned algorithm missing from registry.')

    manifest = REGISTRY[algorithm_key]
    if schema_key not in manifest.supported_schemas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Algorithm '{algorithm_key}' cannot fulfill schema type '{schema_key}'.",
        )
    item_schema, id_field = SCHEMA_REGISTRY[schema_key]
    safe_context_dict = context_data.model_dump()

    try:
        response: EnrichedResponseWrapper = await recommender_service.get_recommendations(
            item_schema=item_schema,
            id_field=id_field,
            ratings=ratings,
            limit=limit,
            context_data=safe_context_dict,
        )
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='There was a problem with the recommender engine. Please contact an administrator.',
        ) from e
    return response
