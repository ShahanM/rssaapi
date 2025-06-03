from sqlalchemy.ext.asyncio import AsyncSession

from data.repositories.page import PageRepository


class StepPageService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.page_repository = PageRepository(db)
