from sqlalchemy.ext.asyncio import AsyncSession

from data.models.survey_constructs import ConstructItem
from data.repositories.base_repo import BaseRepository


class ConstructItemRepository(BaseRepository[ConstructItem]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, ConstructItem)
