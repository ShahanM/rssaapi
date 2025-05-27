import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from data.models.study import StudyCondition
from data.repositories.base_repo import BaseRepository


class StudyConditionRepository(BaseRepository[StudyCondition]):
	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_conditions_by_study_id(self, study_id: uuid.UUID) -> list[StudyCondition]:
		query = select(StudyCondition).where(StudyCondition.study_id == study_id)
		result = await self.db.execute(query)

		return list(result.scalars().all())
