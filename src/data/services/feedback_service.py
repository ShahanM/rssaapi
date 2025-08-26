import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant_responses import Feedback
from data.repositories.feedback import FeedbackRepository
from data.repositories.participant import ParticipantRepository
from data.schemas.feedback_schemas import FeedbackCreateSchema


class FeedbackService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.participant_repo = ParticipantRepository(db)
		self.feedback_repo = FeedbackRepository(db)

	async def create_feedback(self, study_id: uuid.UUID, feedback_data: FeedbackCreateSchema):
		print(feedback_data)
		print(feedback_data.feedback_text)
		feedback_obj = Feedback(
			feedback_data.participant_id,
			study_id,
			feedback_data.feedback_text,
			feedback_data.feedback_type,
			feedback_data.feedback_category,
		)
		_ = await self.feedback_repo.create(feedback_obj)
		await self.db.commit()
