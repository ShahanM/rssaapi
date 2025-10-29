from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.repositories.api_key_repo import ApiKeyRepository
from rssa_api.data.repositories.feedback import FeedbackRepository
from rssa_api.data.repositories.participant_responses.participant_response import (
    FreeformResponseRepository,
    InteractionLoggingRepository,
    ParticipantRatingRepository,
    StudyInteractionResponseRepository,
    SurveyItemResponseRepository,
)
from rssa_api.data.rssadb import get_db

from .demographics import DemographicsRepository
from .participant_movie_session import ParticipantMovieSessionRepository
from .participant_session import ParticipantSessionRepositorty
from .pre_shuffled_movie_list import PreShuffledMovieRepository
from .study_components.page import PageRepository
from .study_components.page_content import PageContentRepository
from .study_components.study import StudyRepository
from .study_components.study_condition import StudyConditionRepository
from .study_components.study_step import StudyStepRepository
from .study_participants.participant import ParticipantRepository
from .study_participants.recommendation_context import ParticipantRecommendationContextRepository
from .user_repo import UserRepository


def get_study_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyRepository:
    return StudyRepository(db)


def get_study_condition_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyConditionRepository:
    return StudyConditionRepository(db)


def get_participant_movie_session_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantMovieSessionRepository:
    return ParticipantMovieSessionRepository(db)


def get_pre_shuffled_movie_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PreShuffledMovieRepository:
    return PreShuffledMovieRepository(db)


def get_participant_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantRepository:
    return ParticipantRepository(db)


def get_demographics_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DemographicsRepository:
    return DemographicsRepository(db)


def get_page_content_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PageContentRepository:
    return PageContentRepository(db)


def get_page_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PageRepository:
    return PageRepository(db)


def get_study_step_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyStepRepository:
    return StudyStepRepository(db)


def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)


def get_participant_session_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantSessionRepositorty:
    return ParticipantSessionRepositorty(db)


def get_api_key_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKeyRepository:
    return ApiKeyRepository(db)


def get_item_response_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SurveyItemResponseRepository:
    return SurveyItemResponseRepository(db)


def get_text_reponse_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FreeformResponseRepository:
    return FreeformResponseRepository(db)


def get_content_rating_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantRatingRepository:
    return ParticipantRatingRepository(db)


def get_interaction_loggin_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> InteractionLoggingRepository:
    return InteractionLoggingRepository(db)


def get_feedback_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> FeedbackRepository:
    return FeedbackRepository(db)


def get_study_interaction_response_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyInteractionResponseRepository:
    return StudyInteractionResponseRepository(db)


def get_participant_recommendation_context_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParticipantRecommendationContextRepository:
    return ParticipantRecommendationContextRepository(db)
