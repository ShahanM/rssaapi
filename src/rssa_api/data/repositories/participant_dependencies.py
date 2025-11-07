"""Participant Dependencies Repository."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.repositories.study_participants.feedback import FeedbackRepository
from rssa_api.data.rssadb import get_db

from .study_participants.demographics import DemographicsRepository
from .study_participants.participant import ParticipantRepository
from .study_participants.participant_movie_session import ParticipantMovieSessionRepository
from .study_participants.participant_session import ParticipantSessionRepositorty
from .study_participants.recommendation_context import ParticipantRecommendationContextRepository


def get_demographics_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DemographicsRepository:
    """Get DemographicsRepository dependency."""
    return DemographicsRepository(db)


def get_feedback_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> FeedbackRepository:
    """Get FeedbackRepository dependency."""
    return FeedbackRepository(db)


def get_participant_movie_session_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantMovieSessionRepository:
    """Get ParticipantMovieSessionRepository dependency."""
    return ParticipantMovieSessionRepository(db)


def get_participant_session_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantSessionRepositorty:
    """Get ParticipantSessionRepositorty dependency."""
    return ParticipantSessionRepositorty(db)


def get_participant_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantRepository:
    """Get ParticipantRepository dependency."""
    return ParticipantRepository(db)


def get_participant_recommendation_context_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantRecommendationContextRepository:
    """Get ParticipantRecommendationContextRepository dependency."""
    return ParticipantRecommendationContextRepository(db)
