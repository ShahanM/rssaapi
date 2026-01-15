"""Dependency utilities for services."""

from typing import Annotated

from fastapi import Depends
from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.rssadb.repositories.participant_responses import (
    ParticipantFreeformResponseRepository,
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
    ParticipantSurveyResponseRepository,
)
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
    StudyParticipantTypeRepository,
)
from rssa_storage.rssadb.repositories.survey_components import (
    SurveyConstructRepository,
    SurveyItemRepository,
    SurveyScaleLevelRepository,
    SurveyScaleRepository,
)

from rssa_api.data.services.movie_service import MovieService
from rssa_api.data.services.response_service import ParticipantResponseService
from rssa_api.data.services.study_admin import ApiKeyService, PreShuffledMovieService, UserService
from rssa_api.data.services.study_participants import (
    EnrollmentService,
    FeedbackService,
    ParticipantStudySessionService,
    StudyParticipantMovieSessionService,
)
from rssa_api.data.sources.moviedb import get_repository as movie_repo
from rssa_api.data.sources.moviedb import get_service as movie_service
from rssa_api.data.sources.rssadb import get_service as rssa_service

from .study_components import (
    StudyConditionService,
    StudyParticipantService,
    StudyService,
    StudyStepPageContentService,
    StudyStepPageService,
    StudyStepService,
)
from .survey_components import SurveyConstructService, SurveyItemService, SurveyScaleLevelService, SurveyScaleService

# Item services
MovieServiceDep = Annotated[MovieService, Depends(movie_service(MovieService, movie_repo(MovieRepository)))]

# Study component services
StudyServiceDep = Annotated[StudyService, Depends(rssa_service(StudyService, StudyRepository))]
StudyStepServiceDep = Annotated[StudyStepService, Depends(rssa_service(StudyStepService, StudyStepRepository))]
StudyStepPageServiceDep = Annotated[
    StudyStepPageService, Depends(rssa_service(StudyStepPageService, StudyStepPageRepository))
]
StudyStepPageContentServiceDep = Annotated[
    StudyStepPageContentService,
    Depends(rssa_service(StudyStepPageContentService, StudyStepPageContentRepository)),
]
StudyConditionServiceDep = Annotated[
    StudyConditionService,
    Depends(rssa_service(StudyConditionService, StudyConditionRepository)),
]

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
EnrollmentServiceDep = Annotated[
    EnrollmentService,
    Depends(
        rssa_service(
            EnrollmentService, StudyParticipantRepository, StudyParticipantTypeRepository, StudyConditionRepository
        )
    ),
]
StudyParticipantServiceDep = Annotated[
    StudyParticipantService,
    Depends(
        rssa_service(
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
        rssa_service(
            StudyParticipantMovieSessionService, StudyParticipantMovieSessionRepository, PreShuffledMovieRepository
        )
    ),
]
FeedbackServiceDep = Annotated[FeedbackService, Depends(rssa_service(FeedbackService, FeedbackRepository))]
ParticipantStudySessionServiceDep = Annotated[
    ParticipantStudySessionService,
    Depends(rssa_service(ParticipantStudySessionService, ParticipantStudySessionRepository)),
]

# Study admin services
PreShuffledMovieServiceDep = Annotated[
    PreShuffledMovieService, Depends(rssa_service(PreShuffledMovieService, PreShuffledMovieRepository))
]
ApiKeyServiceDep = Annotated[ApiKeyService, Depends(rssa_service(ApiKeyService, ApiKeyRepository))]
UserServiceDep = Annotated[UserService, Depends(rssa_service(UserService, UserRepository))]


ParticipantResponseServiceDep = Annotated[
    ParticipantResponseService,
    Depends(
        rssa_service(
            ParticipantResponseService,
            StudyParticipantRepository,
            ParticipantSurveyResponseRepository,
            ParticipantFreeformResponseRepository,
            ParticipantRatingRepository,
            ParticipantStudyInteractionResponseRepository,
        )
    ),
]
