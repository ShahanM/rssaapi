import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.participant_movie_sequence import ParticipantMovieSession
from rssa_api.data.repositories.base_repo import BaseRepository


class ParticipantMovieSessionRepository(BaseRepository[ParticipantMovieSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ParticipantMovieSession)

    async def get_movie_session_by_participant_id(self, participant_id: uuid.UUID) -> ParticipantMovieSession:
        query = select(ParticipantMovieSession).where(ParticipantMovieSession.participant_id == participant_id)

        db_row = await self.db.execute(query)

        return db_row.scalar_one_or_none()
