from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant_responses import Feedback
from data.repositories.base_repo import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Feedback)
