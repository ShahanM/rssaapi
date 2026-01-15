import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.schemas.recommendations import EnrichedResponseWrapper
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.services.dependencies import RecommenderServiceDep

log = logging.getLogger(__name__)

router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)


@router.post('/', response_model=EnrichedResponseWrapper)
async def get_recommendations(
    recommender_service: RecommenderServiceDep,
    id_token: Annotated[dict, Depends(validate_study_participant)],
    context_data: dict[str, Any] | None = Body(default=None),
):
    """Get recommendations for the current participant.

    Args:
        recommender_service: Service to fetch recommendations.
        id_token: Validated participant token.
        context_data: Optional dictionary for dynamic algorithm parameters (e.g. emotion inputs).
    """
    study_participant_id = id_token['pid']

    if context_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Missing context data.')

    response: EnrichedResponseWrapper = await recommender_service.get_recommendations_for_study_participant(
        study_id=id_token['sid'], study_participant_id=study_participant_id, context_data=context_data
    )

    print('response', response)

    return response
