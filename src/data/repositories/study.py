import uuid
from typing import Optional

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models.study_components import Study
from data.models.study_participants import StudyParticipant
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

	async def get_total_participants(self, study_id: uuid.UUID) -> Optional[Row[tuple[Study, int]]]:
		study_query = (
			select(Study, func.count(StudyParticipant.id).label('total_participants'))
			.join_from(Study, StudyParticipant, Study.id == StudyParticipant.study_id, isouter=True)
			.where(Study.id == study_id)
			.group_by(Study.id, Study.name, Study.description, Study.date_created, Study.created_by, Study.owner)
		)

		study_result = await self.db.execute(study_query)

		return study_result.first()
