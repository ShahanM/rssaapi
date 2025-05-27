import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from data.repositories.page import PageRepository
from data.repositories.study_step import StudyStepRepository
from data.schemas.survey_schemas import SurveyPageSchema


class SurveyService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.page_repository = PageRepository(db)
		self.study_step_repository = StudyStepRepository(db)

	async def get_first_survey_page(self, step_id: uuid.UUID) -> SurveyPageSchema:
		survey_pages = await self.page_repository.get_pages_by_step_id(step_id)

		return SurveyPageSchema.model_validate(survey_pages[0])
