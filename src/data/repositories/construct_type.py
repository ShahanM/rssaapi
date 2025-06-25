from sqlalchemy.ext.asyncio import AsyncSession

from data.models.survey_constructs import ConstructType
from data.repositories.base_repo import BaseRepository


class ConstructTypeRepository(BaseRepository[ConstructType]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, ConstructType)
