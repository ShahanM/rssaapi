"""Router for recommendation endpoints."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.schemas.movie_schemas import ERSMovieSchema, MovieDetailSchema, MovieSchema
from rssa_api.data.schemas.recommendations import RecommendationRequestPayload
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.services.dependencies import RecommenderServiceDep
from rssa_api.services.recommendation.registry import REGISTRY

log = structlog.getLogger(__name__)

router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)

SCHEMA_REGISTRY = {
    'standard': (MovieSchema, 'movielens_id'),
    'standard_emotion': (ERSMovieSchema, 'movielens_id'),
    'detailed': (MovieDetailSchema, 'movielens_id'),
    'community_advisors': (MovieSchema, 'movielens_id'),  # Advisors don't need full details
    'community_comparison': (MovieSchema, 'movielens_id'),  # PrefViz doesn't need full details
    # 'book_standard': (BookSchema, 'isbn'),        # Look how easy future domains are!
}


@router.post('/')
async def get_recommendations(
    recommender_service: RecommenderServiceDep,
    id_token: Annotated[dict, Depends(validate_study_participant)],
    # context_data: dict[str, Any] | None = Body(default=None),
    context_data: RecommendationRequestPayload = Body(...),
):
    """Get recommendations for the current participant.

    Args:
        recommender_service: Service to fetch recommendations.
        id_token: Validated participant token.
        context_data: Optional dictionary for dynamic algorithm parameters (e.g. emotion inputs).
    """
    requested_type = context_data.schema_type
    algorithm_key = await recommender_service.get_participant_algorithm_key(id_token['sub'])

    if algorithm_key not in REGISTRY:
        raise HTTPException(status_code=500, detail='Assigned algorithm missing from registry.')

    manifest = REGISTRY[algorithm_key]
    # requested_type = context_data.get('schema_type', manifest.default_schema)
    requested_type = context_data.schema_type

    if requested_type not in manifest.supported_schemas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Algorithm '{algorithm_key}' cannot fulfill schema type '{requested_type}'.",
        )

    item_schema, id_field = SCHEMA_REGISTRY[requested_type]
    safe_context_dict = context_data.model_dump()
    log.warn('REQTEST', sqte=safe_context_dict)
    try:
        log.warn('REwerweSER')
        response = await recommender_service.get_recommendations_for_study_participant(
            item_schema=item_schema,
            id_field=id_field,
            study_id=id_token['sty'],
            study_participant_id=id_token['sub'],
            context_data=safe_context_dict,
        )
        # log.warn('RESER', terse=response)
    except Exception:
        return {'Error': 'There was a problem with the recommender engine. Please contact an administrator.'}
    # log.warn('REwerweSER', terse=response)
    return response
