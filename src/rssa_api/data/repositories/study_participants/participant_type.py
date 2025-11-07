"""Repository for ParticipantType model."""

from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_participants import ParticipantType
from rssa_api.data.repositories.base_repo import BaseRepository


class ParticipantTypeRepository(BaseRepository[ParticipantType]):
    """Repository for ParticipantType model.

    Attributes:
        db: The database session.
        model: The ParticipantType model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the ParticipantTypeRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, ParticipantType)
