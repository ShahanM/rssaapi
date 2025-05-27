import uuid
from typing import List

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_v2 import Page

from .base_repo import BaseRepository


class PageRepository(BaseRepository[Page]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, Page)

	async def get_pages_by_step_id(self, step_id: uuid.UUID) -> List[Page]:
		query = select(Page).where(Page.step_id == step_id).order_by(asc(Page.order_position))
		result = await self.db.execute(query)
		return list(result.scalars().all())

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
