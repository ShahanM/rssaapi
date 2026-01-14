from typing import Annotated, Any, Optional

from fastapi import APIRouter, Body, Depends

from rssa_api.data.schemas.participant_response_schemas import MovieLensRating
from rssa_api.data.schemas.preferences_schemas import (
    AdvisorProfileSchema,
    Avatar,
)
from rssa_api.data.schemas.recommendations import EnrichedResponseWrapper
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.services.dependencies import RecommenderServiceDep

router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)


@router.post('/', response_model=EnrichedResponseWrapper)
async def get_recommendations(
    recommender_service: RecommenderServiceDep,
    ratings: list[MovieLensRating],
    limit: int,
    context_data: Optional[dict[str, Any]] = Body(default=None),
):
    """Get recommendations for the current participant.

    Args:
        recommender_service: Service to fetch recommendations.
        ratings: List of movielens ids for which recommendations are to be fetched.
        limit: Number of recommendations to fetch.
        context_data: Optional dictionary for dynamic algorithm parameters (e.g. emotion inputs).
    """
    response: EnrichedResponseWrapper = await recommender_service.get_recommendations(
        ratings=ratings, limit=limit, context_data=context_data
    )

    return response
