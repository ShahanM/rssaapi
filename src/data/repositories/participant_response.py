from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant_behavior import ContentRating, InteractionLog
from data.models.participant_responses import FreeformResponse, SurveyItemResponse
from data.repositories.base_repo import BaseRepository


class SurveyItemResponseRepository(BaseRepository[SurveyItemResponse]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SurveyItemResponse)


class FreeformResponseRepository(BaseRepository[FreeformResponse]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, FreeformResponse)


class ContentRatingRepository(BaseRepository[ContentRating]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ContentRating)


class InteractionLoggingRepository(BaseRepository[InteractionLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, InteractionLog)
