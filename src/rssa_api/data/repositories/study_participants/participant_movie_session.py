"""Repository for ParticipantMovieSession model."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.participant_movie_sequence import ParticipantMovieSession
from rssa_api.data.repositories.base_repo import BaseRepository


class ParticipantMovieSessionRepository(BaseRepository[ParticipantMovieSession]):
    """Repository for ParticipantMovieSession model.

    Attributes:
        db: The database session.
        model: The ParticipantMovieSession model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the ParticipantMovieSessionRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, ParticipantMovieSession)

    async def get_movie_session_by_participant_id(self, participant_id: uuid.UUID) -> Optional[ParticipantMovieSession]:
        """Get ParticipantMovieSession by participant ID.

        Args:
            participant_id: The UUID of the study participant.

        Returns:
            The ParticipantMovieSession instance or None if not found.
        """
        query = select(ParticipantMovieSession).where(ParticipantMovieSession.participant_id == participant_id)

        db_row = await self.db.execute(query)

        return db_row.scalar_one_or_none()
