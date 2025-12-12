"""Dependency injection utilities for repositories."""

from typing import Annotated, Callable, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.repositories.participant_responses import (
    ParticipantFreeformResponseRepository,
    ParticipantInteractionLogRepository,
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
    ParticipantSurveyResponseRepository,
)
from rssa_api.data.repositories.study_admin import ApiKeyRepository, PreShuffledMovieRepository, UserRepository
from rssa_api.data.repositories.study_participants import (
    ParticipantDemographicRepository,
    ParticipantRecommendationContextRepository,
    ParticipantStudySessionRepository,
    StudyParticipantMovieSessionRepository,
    StudyParticipantRepository,
)
from rssa_api.data.rssadb import get_db

from .study_components import (
    FeedbackRepository,
    StudyConditionRepository,
    StudyRepository,
    StudyStepPageContentRepository,
    StudyStepPageRepository,
    StudyStepRepository,
)
from .survey_components import (
    SurveyConstructRepository,
    SurveyItemRepository,
    SurveyScaleLevelRepository,
    SurveyScaleRepository,
)

R = TypeVar('R')


def get_repository(repo_constructor: Callable[[AsyncSession], R]) -> Callable[[AsyncSession], R]:
    """Factory to create a dependency for a specific repository type.

    Accepts a class (or function) that takes an AsyncSession and returns R.
    """

    def _get_repo(db: Annotated[AsyncSession, Depends(get_db)]) -> R:
        return repo_constructor(db)

    return _get_repo


get_feedback_repository = get_repository(FeedbackRepository)

# RSSA admin metadata repositories
get_pre_shuffled_movie_repository = get_repository(PreShuffledMovieRepository)
get_user_repository = get_repository(UserRepository)
get_api_key_repository = get_repository(ApiKeyRepository)

# Study component repositories
get_study_repository = get_repository(StudyRepository)
get_study_condition_repository = get_repository(StudyConditionRepository)
get_study_step_repository = get_repository(StudyStepRepository)
StudyStepRepositoryDep = Annotated[StudyStepRepository, Depends(get_study_step_repository)]

get_study_step_page_repository = get_repository(StudyStepPageRepository)
StudyStepPageRepositoryDep = Annotated[StudyStepPageRepository, Depends(get_study_step_page_repository)]

get_study_step_page_content_repository = get_repository(StudyStepPageContentRepository)
StudyStepPageContentRepositoryDep = Annotated[
    StudyStepPageContentRepository, Depends(get_study_step_page_content_repository)
]

# Survey construct repositories
get_survey_construct_repository = get_repository(SurveyConstructRepository)
get_survey_scale_repository = get_repository(SurveyScaleRepository)
get_survey_item_repository = get_repository(SurveyItemRepository)
get_survey_scale_level_repository = get_repository(SurveyScaleLevelRepository)

# Study participant repositories
get_study_participant_repository = get_repository(StudyParticipantRepository)
StudyParticipantRepositoryDep = Annotated[StudyParticipantRepository, Depends(get_study_participant_repository)]

get_study_participant_movie_session_repository = get_repository(StudyParticipantMovieSessionRepository)

# Participant study context repositories
get_participant_study_session_repository = get_repository(ParticipantStudySessionRepository)
get_participant_recommendation_context_repository = get_repository(ParticipantRecommendationContextRepository)

# Participant context repositories
get_participant_demographic_repository = get_repository(ParticipantDemographicRepository)
get_participant_interaction_log_repository = get_repository(ParticipantInteractionLogRepository)

# Participant response repositories
get_participant_freeform_response_repository = get_repository(ParticipantFreeformResponseRepository)
ParticipantFreeformResponseRepositoryDep = Annotated[
    ParticipantFreeformResponseRepository, Depends(get_participant_freeform_response_repository)
]

get_participant_rating_repository = get_repository(ParticipantRatingRepository)
ParticipantRatingRepositoryDep = Annotated[ParticipantRatingRepository, Depends(get_participant_rating_repository)]

get_participant_study_interaction_response_repository = get_repository(ParticipantStudyInteractionResponseRepository)
ParticipantStudyInteractionResponseRepositoryDep = Annotated[
    ParticipantStudyInteractionResponseRepository, Depends(get_participant_study_interaction_response_repository)
]

get_participant_survey_response_repository = get_repository(ParticipantSurveyResponseRepository)
ParticipantSurveyResponseRepositoryDep = Annotated[
    ParticipantSurveyResponseRepository, Depends(get_participant_survey_response_repository)
]
