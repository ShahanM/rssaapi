"""Repositories for participant responses."""

from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.participant_responses import (
    FreeformResponse,
    ParticipantInteractionLog,
    ParticipantRating,
    StudyInteractionResponse,
    SurveyItemResponse,
)
from rssa_api.data.repositories.base_repo import BaseRepository
from rssa_api.data.repositories.participant_responses.base_participant_response_repo import (
    BaseParticipantResponseRepository,
)


class SurveyItemResponseRepository(BaseParticipantResponseRepository[SurveyItemResponse]):
    """Repository for SurveyItemResponse model."""

    def __init__(self, db: AsyncSession):
        """Initialize the SurveyItemResponseRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, SurveyItemResponse)


class FreeformResponseRepository(BaseParticipantResponseRepository[FreeformResponse]):
    """Repository for FreeformResponse model."""

    def __init__(self, db: AsyncSession):
        """Initialize the FreeformResponseRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, FreeformResponse)


class ParticipantRatingRepository(BaseParticipantResponseRepository[ParticipantRating]):
    """Repository for ParticipantRating model."""

    def __init__(self, db: AsyncSession):
        """Initialize the ParticipantRatingRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, ParticipantRating)


class InteractionLoggingRepository(BaseRepository[ParticipantInteractionLog]):
    """Repository for ParticipantInteractionLog model."""

    def __init__(self, db: AsyncSession):
        """Initialize the InteractionLoggingRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, ParticipantInteractionLog)


class StudyInteractionResponseRepository(BaseParticipantResponseRepository[StudyInteractionResponse]):
    """Repository for StudyInteractionResponse model."""

    def __init__(self, db: AsyncSession):
        """Initialize the StudyInteractionResponseRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, StudyInteractionResponse)
