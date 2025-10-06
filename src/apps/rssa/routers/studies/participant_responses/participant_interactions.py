import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from auth.authorization import validate_study_participant
from data.schemas.participant_response_schemas import (
    StudyInteractionResponseBaseSchema,
    StudyInteractionResponseSchema,
)
from data.services.response_service import ParticipantResponseService
from data.services.rssa_dependencies import get_response_service as response_service

interactions_router = APIRouter(
    prefix='/interactions',
    tags=['Participant responses - study interactions'],
)


@interactions_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=StudyInteractionResponseSchema,
    summary='',
    description='',
    response_description='',
)
async def create_interaction_response(
    interaction_response: StudyInteractionResponseBaseSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    int_response = await service.create_participant_interaction_response(
        id_token['sid'], id_token['pid'], interaction_response
    )

    return int_response


@interactions_router.get(
    '/{step_id}',  # FIXME: This should be page_id but currently we only support pages for survey steps
    status_code=status.HTTP_200_OK,
    response_model=list[StudyInteractionResponseSchema],
    summary='',
    description='',
    response_description='',
)
async def get_interaction_responses(
    step_id: uuid.UUID,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    responses = await service.get_participant_interaction_responses(step_id, id_token['sid'], id_token['pid'])

    return responses


@interactions_router.patch(
    '/{interactions_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary='',
    description='',
    response_description='',
)
async def update_interaction_response(
    interactions_id: uuid.UUID,
    update_payload: StudyInteractionResponseSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    _: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    client_version = update_payload.version
    update_successful = await service.update_participant_interaction_response(
        interactions_id, update_payload.model_dump(exclude={'version'}), client_version
    )

    if not update_successful:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Resource version mismatch. Data was updated by another process',
        )
