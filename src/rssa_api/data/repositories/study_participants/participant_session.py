"""Repository for ParticipantSession model."""

from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_participants import ParticipantSession
from rssa_api.data.repositories.base_repo import BaseRepository


class ParticipantStudySessionRepository(BaseRepository[ParticipantSession]):
    """Repository for ParticipantSession model."""

    pass
