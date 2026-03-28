"""Router for participant endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from rssa_api.auth.authorization import decode_jwt, validate_api_key, validate_study_participant
from rssa_api.data.schemas.participant_schemas import (
    DemographicsCreate,
    StudyParticipantReadWithCondition,
)
from rssa_api.data.schemas.telemetry import TelemetryBatchPayload
from rssa_api.data.services.dependencies import StudyParticipantServiceDep, TelemetryServiceDep

router = APIRouter(
    prefix='/participants',
    tags=['Participants'],
    dependencies=[Depends(validate_api_key)],
)


@router.get('/me', response_model=StudyParticipantReadWithCondition, status_code=status.HTTP_200_OK)
async def get_current_participant(
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
    participant_service: StudyParticipantServiceDep,
):
    """Get current participant details.

    Args:
        id_token: Validated participant token.
        participant_service: Service for participant operations.

    Returns:
        Participant details with condition.
    """
    participant = await participant_service.get(id_token['sub'], StudyParticipantReadWithCondition)

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Participant not found.',
        )
    return participant


@router.post('/demographics', response_model=DemographicsCreate, status_code=status.HTTP_201_CREATED)
async def create_participant_demographic_info(
    demographic_data: DemographicsCreate,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
    service: StudyParticipantServiceDep,
):
    """Create participant demographic info.

    Args:
        demographic_data: Demographic information.
        id_token: Validated participant token.
        service: Service for participant operations.

    Returns:
        Created demographic info.
    """
    dem_data = await service.create_demographic_info(id_token['sub'], demographic_data)

    if not dem_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Something went wrong, could not record demographic data.',
        )
    return dem_data


@router.post(
    '/telemetry',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=None,
    summary='Participant implicit behavior',
    description='Ingests batched telemetry events from the client and processes them in the background.',
)
async def log_study_telemetry(
    payload: TelemetryBatchPayload,
    background_tasks: BackgroundTasks,
    token_content: Annotated[dict, Depends(decode_jwt)],
    telemetry_service: TelemetryServiceDep,
):
    """Store implicit beahvior telemetry.

    Args:
        payload: event logs as JSON string.
        background_tasks: dependency to run the ingestion as a background task.
        token_content: Validated participant token.
        telemetry_service: service dependency to access the repository.
    """
    participant_id = uuid.UUID(token_content.get('sub'))
    session_id = uuid.UUID(token_content.get('sid'))
    study_id = uuid.UUID(token_content.get('sty'))
    background_tasks.add_task(telemetry_service.process_batch, participant_id, session_id, study_id, payload)

    return {'status': 'accepted', 'queued_events': len(payload.events)}
