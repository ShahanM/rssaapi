"""Response Dependencies Repository."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.repositories.participant_responses.participant_response import (
    FreeformResponseRepository,
    InteractionLoggingRepository,
    ParticipantRatingRepository,
    StudyInteractionResponseRepository,
    SurveyItemResponseRepository,
)
from rssa_api.data.rssadb import get_db


def get_item_response_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SurveyItemResponseRepository:
    """Get SurveyItemResponseRepository dependency."""
    return SurveyItemResponseRepository(db)


def get_text_reponse_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FreeformResponseRepository:
    """Get FreeformResponseRepository dependency."""
    return FreeformResponseRepository(db)


def get_content_rating_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantRatingRepository:
    """Get ParticipantRatingRepository dependency."""
    return ParticipantRatingRepository(db)


def get_interaction_loggin_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> InteractionLoggingRepository:
    """Get InteractionLoggingRepository dependency."""
    return InteractionLoggingRepository(db)


def get_study_interaction_response_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyInteractionResponseRepository:
    """Get StudyInteractionResponseRepository dependency."""
    return StudyInteractionResponseRepository(db)
