"""Repository for ParticipantSession model."""

from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_participants import ParticipantSession
from rssa_api.data.repositories.base_repo import BaseRepository


class ParticipantSessionRepositorty(BaseRepository[ParticipantSession]):
    """Repository for ParticipantSession model.

    Attributes:
        db: The database session.
        model: The ParticipantSession model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the ParticipantSessionRepositorty.

        Args:
            db: The database session.
        """
        super().__init__(db, ParticipantSession)
