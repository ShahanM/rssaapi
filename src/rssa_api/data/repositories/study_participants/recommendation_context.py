"""Repository for ParticipantRecommendationContext model."""

from rssa_api.data.models.study_participants import ParticipantRecommendationContext
from rssa_api.data.repositories.participant_responses.base_participant_response_repo import (
    BaseParticipantResponseRepository,
)


class ParticipantRecommendationContextRepository(BaseParticipantResponseRepository[ParticipantRecommendationContext]):
    """Repository for ParticipantRecommendationContext model."""

    pass
