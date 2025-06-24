from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_participants import Demographic
from data.repositories.base_repo import BaseRepository


class DemographicsRepository(BaseRepository[Demographic]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, Demographic)
