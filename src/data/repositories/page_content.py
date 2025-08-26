from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import PageContent
from data.repositories.base_repo import BaseRepository


class PageContentRepository(BaseRepository[PageContent]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, PageContent)

	async def get_last_page_content(self, page_id) -> PageContent:
		query = select(PageContent).where(PageContent.page_id == page_id).order_by(PageContent.order_position.desc())
		result = await self.db.execute(query)
		last_page = result.scalars().first()

		return last_page
