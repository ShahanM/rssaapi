from sqlalchemy.ext.asyncio import AsyncSession

from data.models.survey_constructs import ConstructItemType
from data.repositories.base_repo import BaseRepository


class ConstructItemTypeRepository(BaseRepository[ConstructItemType]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, ConstructItemType)
