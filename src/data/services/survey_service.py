import uuid
from typing import Optional

from data.models.study_components import Page, PageContent
from data.repositories import PageContentRepository, PageRepository, StudyStepRepository
from data.schemas.survey_construct_schemas import PageContentCreateSchema


class SurveyService:
	def __init__(
		self,
		page_repo: PageRepository,
		step_repo: StudyStepRepository,
		content_repo: PageContentRepository,
	):
		self.content_repo = content_repo
		self.page_repository = page_repo
		self.step_repository = step_repo

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

	async def create_survey_page(self, new_survey_page: PageContentCreateSchema) -> PageContent:
		last_page_content = await self.content_repo.get_last_page_content(new_survey_page.page_id)
		order_position = last_page_content.order_position + 1 if last_page_content else 1
		page_content = PageContent(
			page_id=new_survey_page.page_id,
			content_id=new_survey_page.construct_id,
			scale_id=new_survey_page.scale_id,
			order_position=order_position,
		)

		await self.content_repo.create(page_content)

		return page_content
