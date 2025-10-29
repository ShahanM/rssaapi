from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.repositories.base_repo import BaseRepository


class ParticipantRepository(BaseRepository[StudyParticipant]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, StudyParticipant)
