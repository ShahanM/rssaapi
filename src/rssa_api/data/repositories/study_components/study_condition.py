import uuid

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_components import StudyCondition
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.repositories.base_repo import BaseRepository


class StudyConditionRepository(BaseRepository[StudyCondition]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, StudyCondition)

    async def get_conditions_by_study_id(self, study_id: uuid.UUID) -> list[StudyCondition]:
        query = select(StudyCondition).where(StudyCondition.study_id == study_id)
        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def get_participant_count_by_condition(self, study_id: uuid.UUID) -> list[Row[tuple[uuid.UUID, str, int]]]:
        condition_counts_query = (
            select(
                StudyCondition.id.label('condition_id'),
                StudyCondition.name.label('condition_name'),
                func.count(StudyParticipant.id).label('participant_count'),
            )
            .join(StudyParticipant, StudyParticipant.condition_id == StudyCondition.id, isouter=True)
            .where(StudyCondition.study_id == study_id)
            .group_by(StudyCondition.id, StudyCondition.name)
            .order_by(StudyCondition.name)
        )

        condition_counts_result = await self.db.execute(condition_counts_query)
        condition_counts_rows = condition_counts_result.all()

        return list(condition_counts_rows)
