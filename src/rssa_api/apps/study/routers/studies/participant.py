import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import (
    validate_api_key,
    validate_study_participant,
)
from rssa_api.data.schemas.participant_schemas import (
    DemographicsCreate,
    StudyParticipantReadWithCondition,
)
from rssa_api.data.services import StudyParticipantServiceDep

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
    participant = await participant_service.get_participant_with_condition(id_token['pid'])

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
    participant_service: StudyParticipantServiceDep,
):
    dem_data = await participant_service.create_demographic_info(id_token['pid'], demographic_data)

    if not dem_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Something went wrong, could not record demographic data.',
        )
    return dem_data
