import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from rssa_api.data.schemas.participant_response_schemas import (
    ParticipantFreeformResponseCreate,
    ParticipantFreeformResponseRead,
    ParticipantFreeformResponseUpdate,
)
from rssa_api.data.services import ResponseType
from rssa_api.data.services.dependencies import ParticipantResponseServiceDep

text_response_router = APIRouter(
    prefix='/texts',
    tags=['Participant responses - text'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


@text_response_router.post('/', status_code=status.HTTP_201_CREATED, response_model=ParticipantFreeformResponseRead)
async def create_freeform_text_response(
    text_response: ParticipantFreeformResponseCreate,
    service: ParticipantResponseServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Create a new freeform text response for a study participant.

    Args:
        text_response: The text response data to be created.
        service: The participant response service.
        id_token: The validated study and participant IDs.

    Returns:
        The created text response.
    """
    created_response = await service.create_response(text_response, id_token['sid'], id_token['pid'])
    return created_response


@text_response_router.patch('/{text_response_id}', response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def update_freeform_text_response(
    text_response_id: uuid.UUID,
    text_response: ParticipantFreeformResponseUpdate,
    service: ParticipantResponseServiceDep,
    _: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Update an existing freeform text response for a study participant.

    Args:
        text_response_id: The ID of the text response to be updated.
        text_response: The updated text response data.
        service: The participant response service.
        _: The validated study and participant IDs (not used).

    Returns:
        An empty response indicating successful update.
    """
    client_version = text_response.version
    update_successful = await service.update_response(
        ResponseType.TEXT_RESPONSE, text_response_id, text_response.model_dump(exclude={'version'}), client_version
    )

    if not update_successful:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Text response update conflict. The resource may have been modified by another process.',
        )
    return {}


@text_response_router.get('/', response_model=list[ParticipantFreeformResponseRead])
async def get_participant_text_response(
    page_id: uuid.UUID,
    service: ParticipantResponseServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Retrieve all freeform text responses for a specific study step and participant.

    Args:
        text_response_id: The ID of the text response to retrieve.
        service: The participant response service.
        _: The validated study and participant IDs (not used).

    Returns:
        The text response data for the specified study step and participant.
    """
    text_response = await service.get_response_for_page(
        ResponseType.TEXT_RESPONSE, id_token['sid'], id_token['pid'], page_id
    )

    return text_response


# TODO: decouple patch and include POST
