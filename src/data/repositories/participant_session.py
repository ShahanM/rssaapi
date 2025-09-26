from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_participants import ParticipantSession
from data.repositories.base_repo import BaseRepository


class ParticipantSessionRepositorty(BaseRepository[ParticipantSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ParticipantSession)
