"""Service for managing ParticipantSession operations."""

import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError

from rssa_api.data.models.study_participants import ParticipantSession
from rssa_api.data.repositories.study_participants import ParticipantStudySessionRepository

MAX_RETRIES = 5


class ParticipantStudySessionService:
    """Service for managing ParticipantSession operations.

    Attributes:
        repo: The ParticipantSession repository.
    """

    def __init__(
        self,
        participant_session_repo: ParticipantStudySessionRepository,
    ):
        """Initialize the ParticipantSessionService.

        Args:
            participant_session_repo: The ParticipantSession repository.
        """
        self.repo = participant_session_repo

    async def create_session(self, participant_id: uuid.UUID) -> Optional[ParticipantSession]:
        """Create a new ParticipantSession for the given participant.

        Args:
            participant_id: The ID of the participant.

        Returns:
            The created ParticipantSession, or None if creation failed after retries.
        """
        for _ in range(MAX_RETRIES):
            resume_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

            new_session = ParticipantSession(
                participant_id=participant_id, resume_code=resume_code, expires_at=expires_at
            )
            try:
                await self.repo.create(new_session)
                return new_session
            except IntegrityError:
                await self.repo.db.rollback()
        else:
            return None

    async def get_session_by_resume_code(self, resume_code: str) -> Optional[ParticipantSession]:
        """Retrieve a ParticipantSession by its resume code.

        Args:
            resume_code: The resume code of the session.

        Returns:
            The ParticipantSession if found and valid, else None.
        """
        session = await self.repo.get_by_field('resume_code', resume_code)
        if not session:
            return None
        if session.created_at + timedelta(hours=72) < datetime.now(timezone.utc):
            await self.repo.update(session.id, {'is_active': False})
            return None

        session_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        await self.repo.update(session.id, {'expires_at': session_expires_at})

        return session
