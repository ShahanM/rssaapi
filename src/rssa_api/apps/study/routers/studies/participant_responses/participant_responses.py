import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.apps.study.routers.studies.participant_responses import participant_text_responses
from rssa_api.auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.schemas.participant_response_schemas import (
    TextResponseCreateSchema,
    TextResponseSchema,
)
from rssa_api.data.services.response_service import ParticipantResponseService
from rssa_api.data.services.rssa_dependencies import get_response_service as response_service

from .participant_interactions import interactions_router
from .participant_ratings import ratings_router
from .participant_text_responses import text_response_router
from .survey_responses import survey_router

router = APIRouter(
    prefix='/responses',
    # tags=['Participant responses - text'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


router.include_router(survey_router)
router.include_router(text_response_router)
router.include_router(ratings_router)
router.include_router(interactions_router)
