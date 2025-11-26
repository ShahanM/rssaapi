"""Repository for ParticipantMovieSession model."""

import uuid
from typing import Optional

from sqlalchemy import select

from rssa_api.data.models.participant_movie_sequence import StudyParticipantMovieSession
from rssa_api.data.repositories.base_repo import BaseRepository


class StudyParticipantMovieSessionRepository(BaseRepository[StudyParticipantMovieSession]):
    """Repository for ParticipantMovieSession model."""

    async def get_movie_session_by_participant_id(
        self, participant_id: uuid.UUID
    ) -> Optional[StudyParticipantMovieSession]:
        """Get ParticipantMovieSession by participant ID.

        Args:
            participant_id: The UUID of the study participant.

        Returns:
            The ParticipantMovieSession instance or None if not found.
        """
        query = select(StudyParticipantMovieSession).where(
            StudyParticipantMovieSession.study_participant_id == participant_id
        )

        db_row = await self.db.execute(query)

        return db_row.scalar_one_or_none()
