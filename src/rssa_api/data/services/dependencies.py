"""Dependency utilities for services."""

from typing import Annotated, Callable, TypeVar

from fastapi import Depends

from rssa_api.data.repositories import (
    ParticipantFreeformResponseRepositoryDep,
    ParticipantRatingRepositoryDep,
    ParticipantStudyInteractionResponseRepositoryDep,
    ParticipantSurveyResponseRepositoryDep,
    StudyStepPageContentRepositoryDep,
    StudyStepPageRepositoryDep,
    StudyStepRepositoryDep,
)
from rssa_api.data.repositories.content_dependencies import get_movie_repository
from rssa_api.data.repositories.dependencies import (
    get_api_key_repository,
    get_feedback_repository,
    get_participant_demographic_repository,
    get_participant_recommendation_context_repository,
    get_participant_study_session_repository,
    get_pre_shuffled_movie_repository,
    get_study_condition_repository,
    get_study_participant_movie_session_repository,
    get_study_participant_repository,
    get_study_repository,
    get_study_step_page_content_repository,
    get_study_step_page_repository,
    get_study_step_repository,
    get_survey_construct_repository,
    get_survey_item_repository,
    get_survey_scale_level_repository,
    get_survey_scale_repository,
    get_user_repository,
)
from rssa_api.data.services.items import MovieService
from rssa_api.data.services.participant_responses import ParticipantResponseService
from rssa_api.data.services.study_admin import ApiKeyService, PreShuffledMovieService, UserService
from rssa_api.data.services.study_components import (
    StudyConditionService,
    StudyService,
    StudyStepPageContentService,
    StudyStepPageService,
    StudyStepService,
)
from rssa_api.data.services.study_participants import (
    FeedbackService,
    ParticipantStudySessionService,
    StudyParticipantMovieSessionService,
    StudyParticipantService,
)
from rssa_api.data.services.survey_constructs import (
    SurveyConstructService,
    SurveyItemService,
    SurveyScaleLevelService,
    SurveyScaleService,
)

S = TypeVar('S')  # Generic service type
R = TypeVar('R')  # Generic repository type


def get_simple_service(
    service_constructor: Callable[[R], S],
    repo_dependency: Callable[..., R],
) -> Callable[[R], S]:
    """Factory to 1-to-1 Service to Repository dependencies.

    Args:
            service_constructor: The constructor for the service (e.g., StudyService).
            repo_dependency: The dependency function for the repo (e.g., get_study_repository).
    """

    def _get_service(repo: Annotated[R, Depends(repo_dependency)]) -> S:
        return service_constructor(repo)

    return _get_service


# Item services
get_movie_service = get_simple_service(MovieService, get_movie_repository)
MovieServiceDep = Annotated[MovieService, Depends(get_movie_service)]

# Study component services
get_study_service = get_simple_service(StudyService, get_study_repository)
StudyServiceDep = Annotated[StudyService, Depends(get_study_service)]

get_study_step_service = get_simple_service(StudyStepService, get_study_step_repository)
StudyStepServiceDep = Annotated[StudyStepService, Depends(get_study_step_service)]

get_study_step_page_content_service = get_simple_service(
    StudyStepPageContentService, get_study_step_page_content_repository
)
StudyStepPageContentServiceDep = Annotated[StudyStepPageContentService, Depends(get_study_step_page_content_service)]

get_study_condition_service = get_simple_service(StudyConditionService, get_study_condition_repository)
StudyConditionServiceDep = Annotated[StudyConditionService, Depends(get_study_condition_service)]


def get_study_step_page_service(
    step_repo: StudyStepRepositoryDep,
    page_repo: StudyStepPageRepositoryDep,
    ctnt_repo: StudyStepPageContentRepositoryDep,
) -> StudyStepPageService:
    """Get StepPageService dependency."""
    return StudyStepPageService(page_repo, ctnt_repo, step_repo)


StudyStepPageServiceDep = Annotated[StudyStepPageService, Depends(get_study_step_page_service)]


# Survey construct services
get_survey_construct_service = get_simple_service(SurveyConstructService, get_survey_construct_repository)
SurveyConstructServiceDep = Annotated[SurveyConstructService, Depends(get_survey_construct_service)]

get_survery_item_service = get_simple_service(SurveyItemService, get_survey_item_repository)
SurveyItemServiceDep = Annotated[SurveyItemService, Depends(get_survery_item_service)]

get_survey_scale_service = get_simple_service(SurveyScaleService, get_survey_scale_repository)
SurveyScaleServiceDep = Annotated[SurveyScaleService, Depends(get_survey_scale_service)]

get_survey_scale_level_service = get_simple_service(SurveyScaleLevelService, get_survey_scale_level_repository)
SurveyScaleLevelServiceDep = Annotated[SurveyScaleLevelService, Depends(get_survey_scale_level_service)]

# Participant response services
# TODO


# Study participant services
def get_study_participant_service(
    participant_repo=Depends(get_study_participant_repository),
    study_condition_repo=Depends(get_study_condition_repository),
    demographics_repo=Depends(get_participant_demographic_repository),
    recommendation_context_repo=Depends(get_participant_recommendation_context_repository),
) -> StudyParticipantService:
    """Get ParticipantService dependency."""
    return StudyParticipantService(
        participant_repo,
        study_condition_repo,
        demographics_repo,
        recommendation_context_repo,
    )


StudyParticipantServiceDep = Annotated[StudyParticipantService, Depends(get_study_participant_service)]


def get_study_participant_movie_session_service(
    movie_session_repo=Depends(get_study_participant_movie_session_repository),
    pre_shuffled_movie_repo=Depends(get_pre_shuffled_movie_repository),
) -> StudyParticipantMovieSessionService:
    """Get ParticipantService dependency."""
    return StudyParticipantMovieSessionService(movie_session_repo, pre_shuffled_movie_repo)


StudyParticipantMovieSessionServiceDep = Annotated[
    StudyParticipantMovieSessionService, Depends(get_study_participant_movie_session_service)
]


get_feedback_service = get_simple_service(FeedbackService, get_feedback_repository)
FeedbackServiceDep = Annotated[FeedbackService, Depends(get_feedback_service)]

# Participant study context repositories
get_participant_study_session_service = get_simple_service(
    ParticipantStudySessionService, get_participant_study_session_repository
)
ParticipantStudySessionServiceDep = Annotated[
    ParticipantStudySessionService, Depends(get_participant_study_session_service)
]
# get_participant_recommendation_context_repository = get_repository(ParticipantRecommendationContextRepository)

# # Participant context repositories
# get_participant_demographic_repository = get_repository(ParticipantDemographicRepository)
# get_participant_interaction_log_repository = get_repository(ParticipantInteractionLogRepository)

# # Participant response repositories
# get_participant_freeform_response_repository = get_repository(ParticipantFreeformResponseRepository)
# get_participant_rating_repository = get_repository(ParticipantRatingRepository)
# get_participant_study_interaction_response_repository = get_repository(ParticipantStudyInteractionResponseRepository)
# get_participant_survey_response_repository = get_repository(ParticipantSurveyResponseRepository)


# Study admin services
get_pre_shuffled_movie_service = get_simple_service(PreShuffledMovieService, get_pre_shuffled_movie_repository)
PreShuffledMovieServiceDep = Annotated[PreShuffledMovieService, Depends(get_pre_shuffled_movie_service)]

get_api_key_service = get_simple_service(ApiKeyService, get_api_key_repository)
ApiKeyServiceDep = Annotated[ApiKeyService, Depends(get_api_key_service)]

get_user_service = get_simple_service(UserService, get_user_repository)
UserServiceDep = Annotated[UserService, Depends(get_user_service)]

# def get_survey_service(
#     page_repo: Annotated[StepPageRepository, Depends(get_study_step_page_repository)],
#     step_repo: Annotated[StudyStepRepository, Depends(get_study_step_repository)],
#     content_repo: Annotated[PageContentRepository, Depends(get_page_content_repository)],
# ) -> SurveyService:
#     return SurveyService(page_repo, step_repo, content_repo)

# def get_participant_session_service(
#     participant_session_repo: Annotated[ParticipantSessionRepositorty, Depends(get_participant_session_repository)],
# ) -> ParticipantSessionService:
#     return ParticipantSessionService(participant_session_repo)


def get_response_service(
    item_repo: ParticipantSurveyResponseRepositoryDep,
    text_repo: ParticipantFreeformResponseRepositoryDep,
    rating_repo: ParticipantRatingRepositoryDep,
    interaction_repo: ParticipantStudyInteractionResponseRepositoryDep,
) -> ParticipantResponseService:
    """Get ParticipantResponseService dependency."""
    return ParticipantResponseService(item_repo, text_repo, rating_repo, interaction_repo)


ParticipantResponseServiceDep = Annotated[ParticipantResponseService, Depends(get_response_service)]
