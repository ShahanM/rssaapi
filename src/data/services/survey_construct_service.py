from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.survey_constructs import SurveyConstruct
from data.repositories.survey_construct import SurveyConstructRepository


class SurveyConstructService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.construct_repo = SurveyConstructRepository(db)

	async def get_survey_constructs(self) -> List[SurveyConstruct]:
		return await self.construct_repo.get_all()
