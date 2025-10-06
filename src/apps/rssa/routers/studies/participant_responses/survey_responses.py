import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from data.schemas.participant_response_schemas import (
    SurveyItemResponseBaseSchema,
    SurveyItemResponseSchema,
    SurveyItemResponseUpdatePayload,
)
from data.services.response_service import ParticipantResponseService
from data.services.rssa_dependencies import get_response_service as response_service

survey_router = APIRouter(
    prefix='/survey',
    tags=['Participant responses - survey items'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


@survey_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=SurveyItemResponseSchema,
    summary='',
    description='',
    response_description='',
)
async def create_survey_item_response(
    item_response: SurveyItemResponseBaseSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    new_response = await service.create_item_response(id_token['sid'], id_token['pid'], item_response)

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
    item_response: SurveyItemResponseUpdatePayload,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    _: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    client_version = item_response.version
    update_successful = await service.update_item_response(
        response_item_id, item_response.model_dump(exclude={'version'}), client_version
    )

    if not update_successful:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Resource version mismatch. Data was updated by another process',
        )


@survey_router.get(
    '/{survey_page_id}',
    status_code=status.HTTP_200_OK,
    response_model=list[SurveyItemResponseSchema],
    summary='',
    description='',
    response_description='',
)
async def get_survey_item_response(
    survey_page_id: uuid.UUID,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    item_responses = await service.get_survey_page_response(id_token['sid'], id_token['pid'], survey_page_id)
    return item_responses
