import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import Page, PageContent
from data.repositories.page import PageRepository
from data.repositories.page_content import PageContentRepository
from data.schemas.step_page_schemas import StepPageCreateSchema
from data.schemas.survey_construct_schemas import ConstructLinkSchema, LinkedContentSchema


class StepPageService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.page_repo = PageRepository(db)
		self.content_repo = PageContentRepository(db)

	async def create_step_page(self, new_page: StepPageCreateSchema) -> Page:
		step_page = Page(
			study_id=new_page.study_id,
			step_id=new_page.step_id,
			order_position=new_page.order_position,
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

	async def link_construct_to_page(self, construct_content: ConstructLinkSchema) -> LinkedContentSchema:
		new_page_content = PageContent(
			page_id=construct_content.page_id,
			content_id=construct_content.construct_id,
			order_position=construct_content.order_position,
		)

		await self.content_repo.create(new_page_content)
		await self.db.refresh(new_page_content)

		return new_page_content
