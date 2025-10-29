import uuid
from datetime import datetime, timezone

from rssa_api.data.models.participant_responses import Feedback
from rssa_api.data.repositories.feedback import FeedbackRepository
from rssa_api.data.schemas.feedback_schemas import FeedbackBaseSchema


class FeedbackService:
    def __init__(self, feedback_repo: FeedbackRepository):
        self.repo = feedback_repo

    async def create_or_update_feedback(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, feedback_data: FeedbackBaseSchema
    ) -> None:
        feedback_item = await self.repo.get_by_fields([('study_id', study_id), ('participant_id', participant_id)])
        if feedback_item:
            update_dict = feedback_item.model_dump()
            update_dict['version'] = feedback_item.version + 1
            await self.repo.update(feedback_item.id, update_dict)
        else:
            feedback_obj = Feedback(
                study_id=study_id,
                participant_id=participant_id,
                feedback_text=feedback_data.feedback_text,
                feedback_type=feedback_data.feedback_type,
                feedback_category=feedback_data.feedback_category,
                updated_at=datetime.now(timezone.utc),
                version=1,
            )
            _ = await self.repo.create(feedback_obj)
