from typing import Annotated

from fastapi import Depends

from data.repositories import (
    DemographicsRepository,
    FreeformResponseRepository,
    PageContentRepository,
    PageRepository,
    ParticipantMovieSessionRepository,
    ParticipantRatingRepository,
    ParticipantRepository,
    PreShuffledMovieRepository,
    StudyConditionRepository,
    StudyRepository,
    StudyStepRepository,
    SurveyItemResponseRepository,
    UserRepository,
)
from data.repositories.api_key_repo import ApiKeyRepository
from data.repositories.feedback import FeedbackRepository
from data.repositories.participant_responses.participant_response import StudyInteractionResponseRepository
from data.repositories.participant_session import ParticipantSessionRepositorty
from data.repositories.rssa_dependencies import (
    get_api_key_repository,
    get_content_rating_repository,
    get_demographics_repository,
    get_feedback_repository,
    get_item_response_repository,
    get_page_content_repository,
    get_page_repository,
    get_participant_movie_session_repository,
    get_participant_recommendation_context_repository,
    get_participant_repository,
    get_participant_session_repository,
    get_pre_shuffled_movie_repository,
    get_study_condition_repository,
    get_study_interaction_response_repository,
    get_study_repository,
    get_study_step_repository,
    get_text_reponse_repository,
    get_user_repository,
)
from data.repositories.study_participants.recommendation_context import ParticipantRecommendationContextRepository
from data.services.api_key_service import ApiKeyService
from data.services.feedback_service import FeedbackService
from data.services.response_service import ParticipantResponseService

from .admin_service import AdminService
from .page_content_service import PageContentService
from .participant_movie_sessions import ParticipantMovieSessionService
from .participant_service import ParticipantService
from .participant_session import ParticipantSessionService
from .study_components.step_page_service import StepPageService
from .study_components.study_condition_service import StudyConditionService
from .study_components.study_service import StudyService
from .study_components.study_step_service import StudyStepService
from .survey_service import SurveyService
from .users import UserService


def get_study_condition_service(
    condition_repo: Annotated[StudyConditionRepository, Depends(get_study_condition_repository)],
) -> StudyConditionService:
    return StudyConditionService(condition_repo)


def get_participant_movie_session_service(
    participant_session_repo: Annotated[
        ParticipantMovieSessionRepository, Depends(get_participant_movie_session_repository)
    ],
    pre_shuffled_movies_repo: Annotated[PreShuffledMovieRepository, Depends(get_pre_shuffled_movie_repository)],
) -> ParticipantMovieSessionService:
    return ParticipantMovieSessionService(participant_session_repo, pre_shuffled_movies_repo)


def get_participant_service(
    participant_repo: Annotated[ParticipantRepository, Depends(get_participant_repository)],
    study_condition_repo: Annotated[StudyConditionRepository, Depends(get_study_condition_repository)],
    demographics_repo: Annotated[DemographicsRepository, Depends(get_demographics_repository)],
    recommendation_context_repo: Annotated[
        ParticipantRecommendationContextRepository, Depends(get_participant_recommendation_context_repository)
    ],
) -> ParticipantService:
    return ParticipantService(participant_repo, study_condition_repo, demographics_repo, recommendation_context_repo)


def get_survey_service(
    page_repo: Annotated[PageRepository, Depends(get_page_repository)],
    step_repo: Annotated[StudyStepRepository, Depends(get_study_step_repository)],
    content_repo: Annotated[PageContentRepository, Depends(get_page_content_repository)],
) -> SurveyService:
    return SurveyService(page_repo, step_repo, content_repo)


def get_step_page_service(
    step_repo: Annotated[StudyStepRepository, Depends(get_study_step_repository)],
    page_repo: Annotated[PageRepository, Depends(get_page_repository)],
    content_repo: Annotated[PageContentRepository, Depends(get_page_content_repository)],
) -> StepPageService:
    return StepPageService(page_repo, content_repo, step_repo)


def get_study_service(
    study_repo: Annotated[StudyRepository, Depends(get_study_repository)],
) -> StudyService:
    return StudyService(study_repo)


def get_study_step_service(
    step_repo: Annotated[StudyStepRepository, Depends(get_study_step_repository)],
) -> StudyStepService:
    return StudyStepService(step_repo)


def get_admin_service(
    shuffled_movie_repo: Annotated[PreShuffledMovieRepository, Depends(get_pre_shuffled_movie_repository)],
) -> AdminService:
    return AdminService(shuffled_movie_repo)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo)


def get_content_service(
    content_repo: Annotated[PageContentRepository, Depends(get_page_content_repository)],
) -> PageContentService:
    return PageContentService(content_repo)


def get_participant_session_service(
    participant_session_repo: Annotated[ParticipantSessionRepositorty, Depends(get_participant_session_repository)],
) -> ParticipantSessionService:
    return ParticipantSessionService(participant_session_repo)


def get_api_key_service(
    api_key_repo: Annotated[ApiKeyRepository, Depends(get_api_key_repository)],
) -> ApiKeyService:
    return ApiKeyService(api_key_repo)


def get_response_service(
    item_repo: Annotated[SurveyItemResponseRepository, Depends(get_item_response_repository)],
    text_repo: Annotated[FreeformResponseRepository, Depends(get_text_reponse_repository)],
    rating_repo: Annotated[ParticipantRatingRepository, Depends(get_content_rating_repository)],
    interaction_repo: Annotated[StudyInteractionResponseRepository, Depends(get_study_interaction_response_repository)],
) -> ParticipantResponseService:
    return ParticipantResponseService(item_repo, text_repo, rating_repo, interaction_repo)


def get_feedback_service(
    feedback_repo: Annotated[FeedbackRepository, Depends(get_feedback_repository)],
) -> FeedbackService:
    return FeedbackService(feedback_repo)
