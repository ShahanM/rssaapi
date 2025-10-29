from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_participants import ParticipantType
from data.repositories.base_repo import BaseRepository


class ParticipantTypeRepository(BaseRepository[ParticipantType]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ParticipantType)
