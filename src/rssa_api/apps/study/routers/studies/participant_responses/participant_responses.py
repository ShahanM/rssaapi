"""Router for aggregation of participant response endpoints."""

from fastapi import APIRouter, Depends

from rssa_api.auth.authorization import get_current_participant, validate_api_key

from .participant_interactions import interactions_router
from .participant_ratings import ratings_router
from .participant_text_responses import text_response_router
from .survey_responses import survey_router

router = APIRouter(
    prefix='/responses',
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


router.include_router(survey_router)
router.include_router(text_response_router)
router.include_router(ratings_router)
router.include_router(interactions_router)
