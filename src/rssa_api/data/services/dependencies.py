"""Dependency utilities for services."""

from typing import Annotated

from fastapi import Depends
from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.rssadb.repositories.study_admin import ApiKeyRepository, PreShuffledMovieRepository, UserRepository
from rssa_storage.rssadb.repositories.study_components import (
    FeedbackRepository,
)
from rssa_storage.rssadb.repositories.study_participants import (
    StudyParticipantMovieSessionRepository,
)
from rssa_storage.rssadb.repositories.survey_components import (
    SurveyConstructRepository,
    SurveyItemRepository,
    SurveyScaleLevelRepository,
    SurveyScaleRepository,
)

from rssa_api.data.services.movie_service import MovieService
from rssa_api.data.services.response_service import ParticipantResponseServiceDep
from rssa_api.data.services.study_admin import ApiKeyService, PreShuffledMovieService, UserService
from rssa_api.data.services.study_participants import (
    EnrollmentServiceDep,
    FeedbackService,
    ParticipantStudySessionServiceDep,
    StudyParticipantMovieSessionService,
)
from rssa_api.data.services.telemetry_service import TelemetryServiceDep
from rssa_api.data.sources.moviedb import get_repository as movie_repo
from rssa_api.data.sources.moviedb import get_service as movie_service
from rssa_api.data.sources.rssadb import get_service as rssa_service

from .study_components import (
    StudyAuthorizationServiceDep,
    StudyConditionServiceDep,
    StudyParticipantServiceDep,
    StudyServiceDep,
    StudyStepPageContentServiceDep,
    StudyStepPageServiceDep,
    StudyStepServiceDep,
)
from .survey_components import SurveyConstructService, SurveyItemService, SurveyScaleLevelService, SurveyScaleService

# Item services
MovieServiceDep = Annotated[MovieService, Depends(movie_service(MovieService, movie_repo(MovieRepository)))]


# Survey construct services
SurveyConstructServiceDep = Annotated[
    SurveyConstructService, Depends(rssa_service(SurveyConstructService, SurveyConstructRepository))
]
SurveyItemServiceDep = Annotated[SurveyItemService, Depends(rssa_service(SurveyItemService, SurveyItemRepository))]
SurveyScaleServiceDep = Annotated[SurveyScaleService, Depends(rssa_service(SurveyScaleService, SurveyScaleRepository))]
SurveyScaleLevelServiceDep = Annotated[
    SurveyScaleLevelService, Depends(rssa_service(SurveyScaleLevelService, SurveyScaleLevelRepository))
]


# Study participant services
StudyParticipantMovieSessionServiceDep = Annotated[
    StudyParticipantMovieSessionService,
    Depends(
        rssa_service(
            StudyParticipantMovieSessionService, StudyParticipantMovieSessionRepository, PreShuffledMovieRepository
        )
    ),
]
FeedbackServiceDep = Annotated[FeedbackService, Depends(rssa_service(FeedbackService, FeedbackRepository))]


# Study admin services
PreShuffledMovieServiceDep = Annotated[
    PreShuffledMovieService, Depends(rssa_service(PreShuffledMovieService, PreShuffledMovieRepository))
]
ApiKeyServiceDep = Annotated[ApiKeyService, Depends(rssa_service(ApiKeyService, ApiKeyRepository))]
UserServiceDep = Annotated[UserService, Depends(rssa_service(UserService, UserRepository))]


__all__ = [
    'StudyAuthorizationServiceDep',
    'StudyConditionServiceDep',
    'StudyServiceDep',
    'StudyStepServiceDep',
    'StudyStepPageServiceDep',
    'StudyStepPageContentServiceDep',
    'EnrollmentServiceDep',
    'StudyParticipantServiceDep',
    'ParticipantResponseServiceDep',
    'ParticipantStudySessionServiceDep',
    'TelemetryServiceDep',
]
