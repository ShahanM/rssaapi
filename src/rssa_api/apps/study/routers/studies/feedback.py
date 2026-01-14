"""Router for handling feedback-related endpoints within studies."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from rssa_api.auth.authorization import get_current_participant, validate_api_key
from rssa_api.data.schemas.participant_response_schemas import FeedbackBaseSchema, FeedbackSchema
from rssa_api.data.schemas.participant_schemas import StudyParticipantRead
from rssa_api.data.services import FeedbackServiceDep

router = APIRouter(
    prefix='/feedbacks',
    tags=['Feedbacks'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


@router.post('/', response_model=FeedbackSchema, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackBaseSchema,
    service: FeedbackServiceDep,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipantRead, Depends(get_current_participant)],
):
    """Endpoint to create feedback for a participant in a study.

    Args:
        feedback: The feedback data to be created.
        service: The FeedbackService instance.
        study_id: The ID of the study (extracted from API key).
        participant: The current authenticated study participant.

    Returns:
        The created Feedback object.
    """
    feedback_obj = await service.create_feedback(study_id, participant.id, feedback)

    return FeedbackSchema.model_validate(feedback_obj)


@router.patch('/{feedback_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_feedback(
    feedback_id: uuid.UUID,
    feedback: FeedbackBaseSchema,
    service: FeedbackServiceDep,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipantRead, Depends(get_current_participant)],
):
    """Endpoint to update feedback for a participant in a study.

    Args:
        feedback_id: The ID of the feedback to update.
        feedback: The feedback data to be updated.
        service: The FeedbackService instance.
        study_id: The ID of the study (extracted from API key).
        participant: The current authenticated study participant.

    Returns:
        None
    """
    # BaseService.update takes id and a dict
    await service.update(feedback_id, feedback.model_dump())

    return None
