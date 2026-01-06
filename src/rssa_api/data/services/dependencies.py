"""Dependency utilities for services."""

from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import Depends
from rssa_storage.rssadb.repositories.study_admin import ApiKeyRepository, PreShuffledMovieRepository, UserRepository
from rssa_storage.rssadb.repositories.study_components import (
    FeedbackRepository,
    StudyConditionRepository,
    StudyRepository,
    StudyStepPageContentRepository,
    StudyStepPageRepository,
    StudyStepRepository,
)
from rssa_storage.rssadb.repositories.study_participants import (
    ParticipantDemographicRepository,
    ParticipantRecommendationContextRepository,
    ParticipantStudySessionRepository,
    StudyParticipantMovieSessionRepository,
    StudyParticipantRepository,
)
from rssa_storage.rssadb.repositories.survey_components import (
    SurveyConstructRepository,
    SurveyItemRepository,
    SurveyScaleLevelRepository,
    SurveyScaleRepository,
)
from rssa_storage.shared import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.repositories import (
    ParticipantFreeformResponseRepositoryDep,
    ParticipantRatingRepositoryDep,
    ParticipantStudyInteractionResponseRepositoryDep,
    ParticipantSurveyResponseRepositoryDep,
)
from rssa_api.data.repositories.content_dependencies import get_movie_repository
from rssa_api.data.rssadb import get_db
from rssa_api.data.services.movie_service import MovieService
from rssa_api.data.services.response_service import ParticipantResponseService
from rssa_api.data.services.study_admin import ApiKeyService, PreShuffledMovieService, UserService
from rssa_api.data.services.study_participants import (
    EnrollmentService,
    FeedbackService,
    ParticipantStudySessionService,
    StudyParticipantMovieSessionService,
)

from .base_service import BaseService
from .study_components import (
    StudyConditionService,
    StudyParticipantService,
    StudyService,
    StudyStepPageContentService,
    StudyStepPageService,
    StudyStepService,
)
from .survey_components import SurveyConstructService, SurveyItemService, SurveyScaleLevelService, SurveyScaleService

S = TypeVar('S', bound='BaseService')  # Generic service type
R = TypeVar('R', bound='BaseRepository')  # Generic repository type
RepoConstructor = Callable[[AsyncSession], R]


def get_simple_service(
    service_constructor: Callable[[R], S],
    repo_dependency: Callable[..., R],
) -> Callable[[R], S]:
    """Factory to 1-to-1 Service to Repository dependencies.

    Args:
            service_constructor: The constructor for the service (e.g., StudyService).
            repo_dependency: The dependency function for the repo (e.g., get_study_repository).
            as_annotated_dependency: Return as a dependency injectable object.
    """

    def _get_service(repo: Annotated[R, Depends(repo_dependency)]) -> S:
        return service_constructor(repo)

    return _get_service


def get_service(
    service_constructor: Callable[..., S],
    *repo_constructors: RepoConstructor,
) -> Callable[[AsyncSession], S]:
    """Composite Factory: Creates a Service by first creating its required Repository.

    Args:
        service_constructor: Class of the Service (e.g. StudyService)
        *repo_constructors: One or more repositories in order accepted by the service constructor.
    """

    def _factory(db: Annotated[AsyncSession, Depends(get_db)]) -> S:
        repos = [repo_cls(db) for repo_cls in repo_constructors]
        return service_constructor(*repos)

    return _factory


# Item services
MovieServiceDep = Annotated[MovieService, Depends(get_simple_service(MovieService, get_movie_repository))]

# Study component services
StudyServiceDep = Annotated[StudyService, Depends(get_service(StudyService, StudyRepository))]
StudyStepServiceDep = Annotated[StudyStepService, Depends(get_service(StudyStepService, StudyStepRepository))]
StudyStepPageServiceDep = Annotated[
    StudyStepPageService, Depends(get_service(StudyStepPageService, StudyStepPageRepository))
]
StudyStepPageContentServiceDep = Annotated[
    StudyStepPageContentService,
    Depends(get_service(StudyStepPageContentService, StudyStepPageContentRepository)),
]
StudyConditionServiceDep = Annotated[
    StudyConditionService,
    Depends(get_service(StudyConditionService, StudyConditionRepository)),
]

# Survey construct services
SurveyConstructServiceDep = Annotated[
    SurveyConstructService, Depends(get_service(SurveyConstructService, SurveyConstructRepository))
]
SurveyItemServiceDep = Annotated[SurveyItemService, Depends(get_service(SurveyItemService, SurveyItemRepository))]
SurveyScaleServiceDep = Annotated[SurveyScaleService, Depends(get_service(SurveyScaleService, SurveyScaleRepository))]
SurveyScaleLevelServiceDep = Annotated[
    SurveyScaleLevelService, Depends(get_service(SurveyScaleLevelService, SurveyScaleLevelRepository))
]


# Study participant services
EnrollmentServiceDep = Annotated[
    EnrollmentService,
    Depends(get_service(EnrollmentService, StudyParticipantRepository, StudyConditionRepository)),
]
StudyParticipantServiceDep = Annotated[
    StudyParticipantService,
    Depends(
        get_service(
            StudyParticipantService,
            StudyParticipantRepository,
            ParticipantDemographicRepository,
            ParticipantRecommendationContextRepository,
        )
    ),
]
StudyParticipantMovieSessionServiceDep = Annotated[
    StudyParticipantMovieSessionService,
    Depends(
        get_service(
            StudyParticipantMovieSessionService, StudyParticipantMovieSessionRepository, PreShuffledMovieRepository
        )
    ),
]
FeedbackServiceDep = Annotated[FeedbackService, Depends(get_service(FeedbackService, FeedbackRepository))]
ParticipantStudySessionServiceDep = Annotated[
    ParticipantStudySessionService,
    Depends(get_service(ParticipantStudySessionService, ParticipantStudySessionRepository)),
]

# Study admin services
PreShuffledMovieServiceDep = Annotated[
    PreShuffledMovieService, Depends(get_service(PreShuffledMovieService, PreShuffledMovieRepository))
]
ApiKeyServiceDep = Annotated[ApiKeyService, Depends(get_service(ApiKeyService, ApiKeyRepository))]
UserServiceDep = Annotated[UserService, Depends(get_service(UserService, UserRepository))]


# Participant response service
def get_response_service(
    item_repo: ParticipantSurveyResponseRepositoryDep,
    text_repo: ParticipantFreeformResponseRepositoryDep,
    rating_repo: ParticipantRatingRepositoryDep,
    interaction_repo: ParticipantStudyInteractionResponseRepositoryDep,
) -> ParticipantResponseService:
    """Get ParticipantResponseService dependency."""
    return ParticipantResponseService(item_repo, text_repo, rating_repo, interaction_repo)


ParticipantResponseServiceDep = Annotated[ParticipantResponseService, Depends(get_response_service)]
