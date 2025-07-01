import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models.study_components import Study
from data.repositories.base_repo import BaseRepository


class StudyRepository(BaseRepository[Study]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, Study)

	async def get_detailed_study_object(self, study_id: uuid.UUID) -> Study:
		query = (
			select(Study).options(selectinload(Study.steps), selectinload(Study.conditions)).where(Study.id == study_id)
		)
		results = await self.db.execute(query)
		study = results.scalar_one_or_none()

		return study
