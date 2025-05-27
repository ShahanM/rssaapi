from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_v2 import Page
from data.repositories.page import PageRepository
from data.schemas.step_page_schemas import StepPageCreateSchema


class StepPageService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.page_repository = PageRepository(db)
