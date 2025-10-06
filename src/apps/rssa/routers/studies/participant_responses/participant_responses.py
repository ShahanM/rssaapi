import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from data.models.study_participants import StudyParticipant
from data.schemas.participant_response_schemas import (
    TextResponseCreateSchema,
    TextResponseSchema,
)
from data.services.response_service import ParticipantResponseService
from data.services.rssa_dependencies import get_response_service as response_service

from .participant_interactions import interactions_router
from .participant_ratings import ratings_router
from .survey_responses import survey_router

router = APIRouter(
    prefix='/responses',
    # tags=['Participant responses'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


router.include_router(survey_router)


@router.patch('/text', response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def create_freeform_text_response(
    text_response: TextResponseCreateSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    await service.create_or_update_text_responses(id_token['sid'], id_token['pid'], text_response)
    return {}


@router.get('/text/{studyStep_id}', response_model=list[TextResponseSchema])
async def get_participant_text_response(
    studyStep_id: uuid.UUID,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
):
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')

    text_responses = await service.get_participant_text_responses(study_id, participant.id, studyStep_id)
    print(text_responses)
    return text_responses


router.include_router(ratings_router)
router.include_router(interactions_router)
