"""Repositories for participant responses."""

from rssa_api.data.models.participant_responses import (
    ParticipantFreeformResponse,
    ParticipantInteractionLog,
    ParticipantRating,
    ParticipantStudyInteractionResponse,
    ParticipantSurveyResponse,
)
from rssa_api.data.repositories.base_repo import BaseRepository
from rssa_api.data.repositories.participant_responses.base_participant_response_repo import (
    BaseParticipantResponseRepository,
)


class ParticipantSurveyResponseRepository(BaseParticipantResponseRepository[ParticipantSurveyResponse]):
    """Repository for ParticipantSurveyResponse model."""

    pass


class ParticipantFreeformResponseRepository(BaseParticipantResponseRepository[ParticipantFreeformResponse]):
    """Repository for FreeformResponse model."""

    pass


class ParticipantRatingRepository(BaseParticipantResponseRepository[ParticipantRating]):
    """Repository for ParticipantRating model."""

    pass


class ParticipantInteractionLogRepository(BaseRepository[ParticipantInteractionLog]):
    """Repository for ParticipantInteractionLog model."""

    pass


class ParticipantStudyInteractionResponseRepository(
    BaseParticipantResponseRepository[ParticipantStudyInteractionResponse]
):
    """Repository for ParticipantStudyInteractionResponse model."""

    pass
