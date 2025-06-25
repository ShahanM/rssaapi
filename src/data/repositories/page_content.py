from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import PageContent
from data.repositories.base_repo import BaseRepository


class PageContentRepository(BaseRepository[PageContent]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, PageContent)
