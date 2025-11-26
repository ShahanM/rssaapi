"""Repository for managing StudyCondition entities in the database."""

import uuid

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_components import StudyCondition
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.repositories.base_repo import BaseRepository


class StudyConditionRepository(BaseRepository[StudyCondition]):
    """Repository for StudyCondition model.

    Attributes:
        db: The database session.
        model: The StudyCondition model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the StudyConditionRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, StudyCondition)

    async def get_conditions_by_study_id(self, study_id: uuid.UUID) -> list[StudyCondition]:
        """Get all StudyCondition entries for a specific study.

        Args:
            study_id: The UUID of the study.

        Returns:
            A list of StudyCondition instances.
        """
        query = select(StudyCondition).where(StudyCondition.study_id == study_id)
        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def get_participant_count_by_condition(self, study_id: uuid.UUID) -> list[Row[tuple[uuid.UUID, str, int]]]:
        """Get participant counts grouped by study conditions for a specific study.

        Args:
            study_id: The UUID of the study.

        Returns:
            A list of rows containing condition ID, condition name, and participant count.
        """
        condition_counts_query = (
            select(
                StudyCondition.id.label('study_condition_id'),
                StudyCondition.name.label('study_condition_name'),
                func.count(StudyParticipant.id).label('participant_count'),
            )
            .join(StudyParticipant, StudyParticipant.study_condition_id == StudyCondition.id, isouter=True)
            .where(StudyCondition.study_id == study_id)
            .group_by(StudyCondition.id, StudyCondition.name)
            .order_by(StudyCondition.name)
        )

        condition_counts_result = await self.db.execute(condition_counts_query)
        condition_counts_rows = condition_counts_result.all()

        return list(condition_counts_rows)
