from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant_responses import SurveyFreeformResponse, SurveyItemResponse
from data.repositories.base_repo import BaseRepository


class SurveyItemResponseRepository(BaseRepository[SurveyItemResponse]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, SurveyItemResponse)


class SurveyFreeformResponseRepository(BaseRepository[SurveyFreeformResponse]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, SurveyFreeformResponse)
