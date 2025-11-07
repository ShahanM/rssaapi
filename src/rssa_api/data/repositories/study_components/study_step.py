"""Repository for managing StudyStep entities in the database."""

import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_components import StudyStep

from ..base_ordered_repo import BaseOrderedRepository


class StudyStepRepository(BaseOrderedRepository[StudyStep]):
    """Repository for StudyStep model.

    Attributes:
        db: The database session.
        model: The StudyStep model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the StudyStepRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, StudyStep, parent_id_column_name='study_id')

    async def validate_path_uniqueness(
        self, study_id: uuid.UUID, path: str, exclude_step_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Validate that a StudyStep path is unique within a study, optionally excluding a specific step ID.

        Args:
            study_id: The UUID of the study.
            path: The path to validate.
            exclude_step_id: An optional UUID of a step to exclude from the check.

        Returns:
            True if the path is unique within the study, False otherwise.
        """
        query = select(StudyStep).where(and_(StudyStep.study_id == study_id, StudyStep.path == path))
        if exclude_step_id:
            query = query.where(StudyStep.id != exclude_step_id)

        existing_step = await self.db.execute(query)

        if existing_step.first():
            return False

        return True
