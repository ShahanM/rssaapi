"""Service layer for handling participant feedback operations."""

import uuid
from datetime import datetime, timezone

from rssa_api.data.models.participant_responses import Feedback
from rssa_api.data.repositories.study_components import FeedbackRepository
from rssa_api.data.schemas.participant_response_schemas import FeedbackBaseSchema


class FeedbackService:
    """Service for managing participant feedback operations."""

    def __init__(self, feedback_repo: FeedbackRepository):
        """Initializes the FeedbackService with the given repository.

        Args:
            feedback_repo: Repository for feedback data operations.
        """
        self.repo = feedback_repo

    async def create_feedback(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, feedback_data: FeedbackBaseSchema
    ) -> Feedback:
        """Creates a new feedback entry for a participant in a study.

        Args:
            study_id: The ID of the study.
            participant_id: The ID of the participant providing feedback.
            feedback_data: The feedback data to be stored.

        Returns:
            The created Feedback object.
        """
        feedback_obj = Feedback(
            study_id=study_id,
            step_id=feedback_data.step_id,
            participant_id=participant_id,
            context_tag=feedback_data.context_tag,
            feedback_text=feedback_data.feedback_text,
            feedback_type=feedback_data.feedback_type,
            feedback_category=feedback_data.feedback_category,
            updated_at=datetime.now(timezone.utc),
            version=1,
        )
        feedback_item = await self.repo.create(feedback_obj)

        return feedback_item
