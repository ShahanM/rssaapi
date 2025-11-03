import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.schemas.participant_response_schemas import (
    TextResponseCreateSchema,
    TextResponseSchema,
)
from rssa_api.data.services.response_service import ParticipantResponseService
from rssa_api.data.services.rssa_dependencies import get_response_service as response_service

text_response_router = APIRouter(
    prefix='/texts',
    tags=['Participant responses - text'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


@text_response_router.patch('/text', response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def create_freeform_text_response(
    text_response: TextResponseCreateSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    await service.create_or_update_text_responses(id_token['sid'], id_token['pid'], text_response)
    return {}


@text_response_router.get('/text/{studyStep_id}', response_model=list[TextResponseSchema])
async def get_participant_text_response(
    studyStep_id: uuid.UUID,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
):
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')

    text_responses = await service.get_participant_text_responses(study_id, participant.id, studyStep_id)
    return text_responses


# TODO: decouple patch and include POST
