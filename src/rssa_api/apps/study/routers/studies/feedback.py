import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from rssa_api.auth.authorization import get_current_participant, validate_api_key
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.rssadb import get_db as rssa_db
from rssa_api.data.schemas.feedback_schemas import FeedbackBaseSchema
from rssa_api.data.services.feedback_service import FeedbackService
from rssa_api.data.services.rssa_dependencies import get_feedback_service as feedback_service
from rssa_api.docs.rssa_docs import Tags

router = APIRouter(
    prefix='/feedbacks',
    tags=['Feedbacks'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


@router.patch('/', response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def create_feedback(
    feedback: FeedbackBaseSchema,
    service: Annotated[FeedbackService, Depends(feedback_service)],
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
):
    await service.create_or_update_feedback(study_id, participant.id, feedback)

    return {}
