import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from auth.authorization import get_current_participant, validate_api_key
from data.models.study_participants import StudyParticipant
from data.schemas.participant_response_schemas import (
    RatedItemBaseSchema,
    RatedItemSchema,
    SurveyItemResponseBaseSchema,
    TextResponseCreateSchema,
    TextResponseSchema,
)
from data.services.response_service import ParticipantResponseService
from data.services.rssa_dependencies import get_response_service as response_service
from docs.rssa_docs import Tags

router = APIRouter(
    prefix='/responses',
    tags=[Tags.response],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


@router.patch(
    '/survey',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary='',
    description='',
    response_description='',
)
async def create_survey_item_response(
    item_response: SurveyItemResponseBaseSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
):
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')
    await service.create_or_update_item_response(study_id, participant.id, item_response)

    return {}


@router.patch('/text', response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def create_freeform_text_response(
    text_response: TextResponseCreateSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
):
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')

    await service.create_or_update_text_responses(study_id, participant.id, text_response)
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


@router.patch(
    '/ratings',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary='',
    description='',
    response_description='',
)
async def create_content_rating(
    rating: RatedItemBaseSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
):
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')

    await service.create_or_update_content_rating(participant.id, rating)

    return {}


@router.get(
    '/ratings',
    response_model=list[RatedItemSchema],
    summary='',
    description='',
    response_description='',
)
async def get_user_ratings(
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
    service: Annotated[ParticipantResponseService, Depends(response_service)],
):
    if participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Permission denied.')

    ratings = await service.get_ratings_for_participants(participant.id)
    return ratings
