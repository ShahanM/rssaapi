import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_components import StudyStep

from ..base_ordered_repo import BaseOrderedRepository


class StudyStepRepository(BaseOrderedRepository[StudyStep]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, StudyStep, parent_id_column_name='study_id')

    async def validate_path_uniqueness(
        self, study_id: uuid.UUID, path: str, exclude_step_id: Optional[uuid.UUID] = None
    ) -> bool:
        query = select(StudyStep).where(and_(StudyStep.study_id == study_id, StudyStep.path == path))
        if exclude_step_id:
            query = query.where(StudyStep.id != exclude_step_id)

        existing_step = await self.db.execute(query)

        if existing_step.first():
            return False

        return True
