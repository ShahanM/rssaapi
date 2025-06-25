from sqlalchemy.ext.asyncio import AsyncSession

from data.models.survey_constructs import SurveyConstruct
from data.repositories.base_repo import BaseRepository


class SurveyConstructRepository(BaseRepository[SurveyConstruct]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, SurveyConstruct)
