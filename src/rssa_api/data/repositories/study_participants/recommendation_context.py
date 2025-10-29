from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_participants import ParticipantRecommendationContext
from rssa_api.data.repositories.base_participant_response_repo import BaseParticipantResponseRepository


class ParticipantRecommendationContextRepository(BaseParticipantResponseRepository[ParticipantRecommendationContext]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ParticipantRecommendationContext)
