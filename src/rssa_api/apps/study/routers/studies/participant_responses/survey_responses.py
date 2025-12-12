import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from rssa_api.data.schemas.participant_response_schemas import (
    ParticipantSurveyResponseCreate,
    ParticipantSurveyResponseRead,
    ParticipantSurveyResponseUpdate,
)
from rssa_api.data.services import ParticipantResponseServiceDep, ResponseType

survey_router = APIRouter(
    prefix='/survey',
    tags=['Participant responses - survey items'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


@survey_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=ParticipantSurveyResponseRead,
    summary='',
    description='',
    response_description='',
)
async def create_survey_item_response(
    item_response: ParticipantSurveyResponseCreate,
    service: ParticipantResponseServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    new_response = await service.create_response(item_response, id_token['sid'], id_token['pid'])

    return new_response


@survey_router.patch(
    '/{response_item_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary='',
    description='',
    response_description='',
)
async def update_survey_item_response(
    response_item_id: uuid.UUID,
    item_response: ParticipantSurveyResponseUpdate,
    service: ParticipantResponseServiceDep,
    _: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    client_version = item_response.version
    update_successful = await service.update_response(
        ResponseType.SURVEY_ITEM, response_item_id, item_response.model_dump(exclude={'version'}), client_version
    )

    if not update_successful:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Resource version mismatch. Data was updated by another process',
        )


@survey_router.get(
    '/{survey_page_id}',
    status_code=status.HTTP_200_OK,
    response_model=list[ParticipantSurveyResponseRead],
    summary='',
    description='',
    response_description='',
)
async def get_survey_item_response(
    survey_page_id: uuid.UUID,
    service: ParticipantResponseServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    item_responses = await service.get_response_for_page(
        ResponseType.SURVEY_ITEM, id_token['sid'], id_token['pid'], survey_page_id
    )
    return item_responses
