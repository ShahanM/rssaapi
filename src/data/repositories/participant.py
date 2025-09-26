from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_participants import (
    StudyParticipant,
)
from data.repositories.base_repo import BaseRepository


class ParticipantRepository(BaseRepository[StudyParticipant]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, StudyParticipant)
