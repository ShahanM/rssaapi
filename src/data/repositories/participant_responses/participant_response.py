import uuid
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant_responses import (
    FreeformResponse,
    ParticipantInteractionLog,
    ParticipantRating,
    StudyInteractionResponse,
    SurveyItemResponse,
)
from data.repositories.base_participant_response_repo import BaseParticipantResponseRepository
from data.repositories.base_repo import BaseRepository


class SurveyItemResponseRepository(BaseParticipantResponseRepository[SurveyItemResponse]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SurveyItemResponse)

    # async def update_response(self, item_id: uuid.UUID, update_payload: dict[str, Any], client_version: int) -> bool:
    #     update_fields = {**update_payload, 'version': client_version + 1}
    #     update_stmt = (
    #         update(SurveyItemResponse)
    #         .where(SurveyItemResponse.id == item_id, SurveyItemResponse.version == client_version)
    #         .values(**update_fields)
    #     )

    #     result = await self.db.execute(update_stmt)

    #     if result.rowcount == 1:
    #         await self.db.commit()
    #         return True
    #     else:
    #         await self.db.rollback()
    #         return False


class FreeformResponseRepository(BaseRepository[FreeformResponse]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, FreeformResponse)


class ParticipantRatingRepository(BaseParticipantResponseRepository[ParticipantRating]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ParticipantRating)


class InteractionLoggingRepository(BaseRepository[ParticipantInteractionLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ParticipantInteractionLog)


class StudyInteractionResponseRepository(BaseParticipantResponseRepository[StudyInteractionResponse]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, StudyInteractionResponse)
