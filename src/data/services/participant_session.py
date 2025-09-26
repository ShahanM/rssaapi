import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError

from data.models.study_participants import ParticipantSession
from data.repositories.participant_session import ParticipantSessionRepositorty

MAX_RETRIES = 5


class ParticipantSessionService:
    def __init__(
        self,
        participant_session_repo: ParticipantSessionRepositorty,
    ):
        self.repo = participant_session_repo

    async def create_session(self, participant_id: uuid.UUID) -> Optional[ParticipantSession]:
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
        session = await self.repo.get_by_field('resume_code', resume_code)
        if not session:
            return None
        return session
