"""Router for handling participant interaction responses in studies."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.schemas.participant_response_schemas import (
    ParticipantStudyInteractionResponseCreate,
    ParticipantStudyInteractionResponseRead,
    ParticipantStudyInteractionResponseUpdate,
)
from rssa_api.data.services import ParticipantResponseServiceDep, ResponseType

interactions_router = APIRouter(
    prefix='/interactions',
    tags=['Participant responses - study interactions'],
)


@interactions_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=ParticipantStudyInteractionResponseRead,
)
async def create_interaction_response(
    interaction_response: ParticipantStudyInteractionResponseCreate,
    service: ParticipantResponseServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Create a new participant interaction response.

    Args:
        interaction_response: The interaction response data.
        service: The participant response service.
        id_token: The validated study participant ID token.

    Returns:
        The created StudyInteractionResponseSchema object.
    """
    int_response = await service.create_response(interaction_response, id_token['sid'], id_token['pid'])

    return int_response


@interactions_router.get(
    '/{page_id}',  # FIXME: This should be page_id but currently we only support pages for survey steps
    status_code=status.HTTP_200_OK,
    response_model=list[ParticipantStudyInteractionResponseRead],
)
async def get_interaction_responses(
    page_id: uuid.UUID,
    service: ParticipantResponseServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Retrieve participant interaction responses for a specific step.

    Args:
        step_id: The ID of the step.
        service: The participant response service.
        id_token: The validated study participant ID token.

    Returns:
        A list of StudyInteractionResponseSchema objects.
    """
    responses = await service.get_response_for_page(
        ResponseType.STUDY_INTERACTION, id_token['sid'], id_token['pid'], page_id
    )

    return responses


@interactions_router.patch(
    '/{interactions_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def update_interaction_response(
    interactions_id: uuid.UUID,
    update_payload: ParticipantStudyInteractionResponseUpdate,
    service: ParticipantResponseServiceDep,
    _: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Update an existing participant interaction response.

    Args:
        interactions_id: The ID of the interaction response to update.
        update_payload: The updated interaction response data.
        service: The participant response service.
        _: The validated study participant ID token.

    Raises:
        HTTPException: If there is a version conflict during the update.
    """
    client_version = update_payload.version
    update_successful = await service.update_response(
        ResponseType.STUDY_INTERACTION, interactions_id, update_payload.model_dump(exclude={'version'}), client_version
    )

    if not update_successful:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Resource version mismatch. Data was updated by another process',
        )
