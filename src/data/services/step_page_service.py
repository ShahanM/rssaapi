import uuid

from data.models.study_components import Page
from data.repositories import PageContentRepository, PageRepository, StudyStepRepository
from data.schemas.step_page_schemas import StepPageCreateSchema


class StepPageService:
	def __init__(
		self,
		page_repo: PageRepository,
		content_repo: PageContentRepository,
		step_repo: StudyStepRepository,
	):
		self.page_repo = page_repo
		self.content_repo = content_repo
		self.step_repo = step_repo

	async def create_step_page(self, new_page: StepPageCreateSchema) -> None:
		survey_step = await self.step_repo.get(new_page.step_id)
		if not survey_step or survey_step.step_type != 'survey':
			raise InvalidComponentType(message='Step not a valid survey step.')

		last_page = await self.page_repo.get_last_page_in_step(new_page.step_id)
		next_order_pos = 1 if last_page is None else last_page.order_position + 1
		step_page = Page(
			study_id=new_page.study_id,
			step_id=new_page.step_id,
			order_position=next_order_pos,
			name=new_page.name,
			description=new_page.description,
		)

		await self.page_repo.create(step_page)

	async def get_step_page(self, page_id: uuid.UUID) -> Page:
		return await self.page_repo.get(page_id)

	async def get_page_with_content_detail(self, page_id: uuid.UUID) -> Page:
		return await self.page_repo.get_page_with_content_detail(page_id)

	async def update_step_page(self, page_id: uuid.UUID, updated_page: dict[str, str]) -> None:
		await self.page_repo.update(page_id, updated_page)


class InvalidComponentType(Exception):
	def __init__(self, message='Invalid component type', value=None):
		super().__init__(message)
		self.value = value
