import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pyparsing import Dict

from auth.authorization import authorize_api_key_for_study, get_current_participant, validate_api_key
from data.models.study_participants import StudyParticipant
from data.schemas.base_schemas import UpdatePayloadSchema
from data.schemas.participant_schemas import DemographicsBaseSchema, ParticipantSchema
from data.services.participant_service import ParticipantService
from data.services.rssa_dependencies import get_participant_service
from docs.rssa_docs import Tags

router = APIRouter(
    prefix='/participants',
    tags=[Tags.participant],
    dependencies=[Depends(validate_api_key)],
)


# @router.patch('/{participant_id}', response_model=ParticipantSchema)
# async def update_participant(
#     participant_id: uuid.UUID,
#     update_data: UpdatePayloadSchema,
#     participant_service: Annotated[ParticipantService, Depends(get_participant_service)],
# ):
#     updated = await participant_service.update_study_participant(participant_id, update_data)

#     return updated


@router.patch('/demographics', response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def create_particpant_demographic_info(
    demographic_data: DemographicsBaseSchema,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
    participant_service: Annotated[ParticipantService, Depends(get_participant_service)],
):
    # print(demographic_data)
    await participant_service.create_or_update_demographic_info(participant.id, demographic_data)
