import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import Page
from data.repositories.page import PageRepository
from data.repositories.study_step import StudyStepRepository


class SurveyService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.page_repository = PageRepository(db)
		self.study_step_repository = StudyStepRepository(db)

	async def get_first_survey_page(self, step_id: uuid.UUID) -> Optional[Page]:
		first_page = await self.page_repository.get_first_page_in_step(step_id)

		return first_page

	async def get_next_survey_page(self, study_id: uuid.UUID, current_page_id: uuid.UUID) -> Optional[Page]:
		current_page = await self.page_repository.get_page_with_full_details(current_page_id)

		if not current_page or current_page.study_id != study_id:
			return None

		next_page = await self.page_repository.get_page_by_step_next_order(
			step_id=current_page.step_id, current_order_position=current_page.order_position
		)
		return next_page

	async def is_last_page_in_step(self, page: Page) -> bool:
		"""
		Determines if a given page is the last page within its step.
		"""
		return not await self.page_repository.has_subsequent_page(page.step_id, page.order_position)
