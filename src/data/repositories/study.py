from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import Study
from data.repositories.base_repo import BaseRepository


class StudyRepository(BaseRepository[Study]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, Study)
