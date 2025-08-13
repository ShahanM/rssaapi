import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import Page
from data.repositories.page import PageRepository
from data.repositories.page_content import PageContentRepository
from data.schemas.step_page_schemas import StepPageCreateSchema


class StepPageService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.page_repo = PageRepository(db)
		self.content_repo = PageContentRepository(db)

	async def create_step_page(self, new_page: StepPageCreateSchema) -> Page:
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
		await self.db.refresh(step_page)

		return step_page

	async def get_step_page(self, page_id: uuid.UUID) -> Page:
		return await self.page_repo.get(page_id)

	async def get_page_with_content_detail(self, page_id: uuid.UUID) -> Page:
		return await self.page_repo.get_page_with_content_detail(page_id)
