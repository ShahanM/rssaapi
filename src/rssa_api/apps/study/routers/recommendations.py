"""Router for recommendation endpoints."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.schemas.recommendations import RecommendationRequestPayload
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.recommenders.registry import REGISTRY, SCHEMA_REGISTRY
from rssa_api.services.dependencies import RecommenderServiceDep

log = structlog.getLogger(__name__)

router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)


@router.post('/')
async def get_recommendations(
    recommender_service: RecommenderServiceDep,
    id_token: Annotated[dict, Depends(validate_study_participant)],
    context_data: RecommendationRequestPayload = Body(...),
):
    """Get recommendations for the current participant."""
    schema_key = context_data.schema_type  # FIXME: Consider changing the name schema_type to something appropriate
    algorithm_key = await recommender_service.get_participant_algorithm_key(id_token['sub'])

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

    if manifest.variant:
        item_schema = item_schema[manifest.variant]

    try:
        response = await recommender_service.get_recommendations_for_study_participant(
            item_schema=item_schema,
            id_field=id_field,
            study_id=id_token['sty'],
            study_participant_id=id_token['sub'],
            context_data=safe_context_dict,
        )
    except Exception as e:
        log.error(e)
        return {'Error': 'There was a problem with the recommender engine. Please contact an administrator.'}
    return response
