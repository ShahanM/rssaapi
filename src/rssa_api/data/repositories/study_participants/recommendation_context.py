"""Repository for ParticipantRecommendationContext model."""

from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_participants import ParticipantRecommendationContext
from rssa_api.data.repositories.participant_responses.base_participant_response_repo import (
    BaseParticipantResponseRepository,
)


class ParticipantRecommendationContextRepository(BaseParticipantResponseRepository[ParticipantRecommendationContext]):
    """Repository for ParticipantRecommendationContext model.

    Attributes:
        db: The database session.
        model: The ParticipantRecommendationContext model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the ParticipantRecommendationContextRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, ParticipantRecommendationContext)
