import uuid
from typing import List, Optional, Union

from sqlalchemy import and_, asc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models.study_components import Page, PageContent
from data.models.survey_constructs import ConstructScale, SurveyConstruct

from .base_repo import BaseRepository


class PageRepository(BaseRepository[Page]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, Page)

	async def get_pages_by_step_id(self, step_id: uuid.UUID) -> List[Page]:
		query = select(Page).where(Page.step_id == step_id).order_by(asc(Page.order_position))
		result = await self.db.execute(query)
		return list(result.scalars().all())

	async def get_page_order_position(self, page_id: uuid.UUID, step_id: uuid.UUID) -> Optional[int]:
		"""
		Fetches only the order_position of a specific page within a step
		"""
		query = select(Page.order_position).where(Page.id == page_id).where(Page.step_id == step_id).limit(1)
		result = await self.db.execute(query)
		return result.scalar_one_or_none()

	async def get_page_with_full_details(self, page_id: uuid.UUID) -> Optional[Page]:
		"""Fetched a Page object along with its associated PageContent
		and their respective SurveyConstruct details.
		"""
		query = (
			select(Page)
			.where(Page.id == page_id)
			.options(
				selectinload(Page.page_contents)
				.selectinload(PageContent.survey_construct)
				.selectinload(SurveyConstruct.items)
			)
		)
		result = await self.db.execute(query)
		page_instance = result.scalar_one_or_none()
		return page_instance

	async def get_first_page_in_step(self, step_id: uuid.UUID) -> Optional[Page]:
		query = (
			select(Page)
			.where(Page.step_id == step_id)
			.order_by(Page.order_position.asc())
			.limit(1)
			.options(
				selectinload(Page.page_contents)
				.selectinload(PageContent.survey_construct)
				.selectinload(SurveyConstruct.items),
				selectinload(Page.page_contents)
				.selectinload(PageContent.construct_scale)
				.selectinload(ConstructScale.scale_levels),
			)
		)
		result = await self.db.execute(query)
		return result.scalar_one_or_none()

	async def get_page_by_step_next_order(self, step_id: uuid.UUID, current_order_position: int) -> Optional[Page]:
		"""
		Fetches the next page within a step based on order_position,
		with all its related details eagerly loaded.
		"""
		query = (
			select(Page)
			.where(Page.step_id == step_id)
			.where(Page.order_position > current_order_position)
			.order_by(Page.order_position.asc())
			.limit(1)
			.options(
				selectinload(Page.page_contents)
				.selectinload(PageContent.survey_construct)
				.selectinload(SurveyConstruct.items),
				selectinload(Page.page_contents)
				.selectinload(PageContent.survey_construct)
				.selectinload(SurveyConstruct.construct_scale)
				.selectinload(ConstructScale.scale_levels),
			)
		)
		result = await self.db.execute(query)
		return result.scalar_one_or_none()

	async def get_page_with_content_detail(self, page_id: uuid.UUID) -> Page:
		query = (
			select(Page)
			.where(Page.id == page_id)
			.order_by(Page.order_position.asc())
			.options(
				selectinload(Page.page_contents)
				.selectinload(PageContent.survey_construct)
				.selectinload(SurveyConstruct.items),
				selectinload(Page.page_contents).selectinload(PageContent.survey_construct),
				selectinload(Page.page_contents)
				.selectinload(PageContent.construct_scale)
				.selectinload(ConstructScale.scale_levels),
			)
		)
		result = await self.db.execute(query)
		return result.scalar_one_or_none()

	async def has_subsequent_page(self, step_id: uuid.UUID, current_order_position: int) -> bool:
		"""
		Checks if there is any page with a higher order_position in the given step.
		This is used to determine if a page is the 'last_page'.
		"""
		stmt = (
			select(Page.id)
			.where(  # Select just the ID for efficiency
				and_(Page.step_id == step_id, Page.order_position > current_order_position)
			)
			.limit(1)
		)  # We only need to know if at least one exists
		result = await self.db.execute(stmt)
		return result.scalars().first() is not None  # Returns True if a subsequent page exists, False otherwise

	async def get_last_page_in_step(self, step_id: uuid.UUID) -> Union[Page, None]:
		query = select(Page).where(Page.study_id == step_id).order_by(Page.order_position.desc())
		result = await self.db.execute(query)
		step = result.scalars().first()

		return step

	async def copy_pages_from(
		self, from_step_id: uuid.UUID, to_step_id: uuid.UUID, new_study_id: uuid.UUID
	) -> List[Page]:
		pages_to_copy = await self.get_pages_by_step_id(from_step_id)
		new_pages = []
		for page in pages_to_copy:
			new_page = Page(
				name=page.c.name,
				order_position=page.c.order_position,
				description=page.c.description,
				study_id=new_study_id,
				step_id=to_step_id,
			)
			self.db.add(new_page)
			new_pages.append(new_page)
		await self.db.commit()
		for page in new_pages:
			await self.db.refresh(page)
		return new_pages
