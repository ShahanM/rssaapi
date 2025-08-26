from typing import Annotated

from fastapi import Depends

from data.repositories import (
	DemographicsRepository,
	PageContentRepository,
	PageRepository,
	ParticipantMovieSessionRepository,
	ParticipantRepository,
	PreShuffledMovieRepository,
	StudyConditionRepository,
	StudyRepository,
	StudyStepRepository,
)
from data.repositories.rssa_dependencies import (
	get_demographics_repository,
	get_page_content_repository,
	get_page_repository,
	get_participant_repository,
	get_participant_session_repository,
	get_pre_shuffled_movie_repository,
	get_study_condition_repository,
	get_study_repository,
	get_study_step_repository,
)

from .admin_service import AdminService
from .participant_service import ParticipantService
from .participant_session_service import ParticipantSessionService
from .step_page_service import StepPageService
from .study_condition_service import StudyConditionService
from .study_service import StudyService
from .study_step_service import StudyStepService
from .survey_service import SurveyService


def get_study_condition_service(
	study_repo: Annotated[StudyRepository, Depends(get_study_repository)],
	condition_repo: Annotated[StudyConditionRepository, Depends(get_study_condition_repository)],
) -> StudyConditionService:
	return StudyConditionService(study_repo, condition_repo)


def get_participant_session_service(
	participant_session_repo: Annotated[ParticipantMovieSessionRepository, Depends(get_participant_session_repository)],
	pre_shuffled_movies_repo: Annotated[PreShuffledMovieRepository, Depends(get_pre_shuffled_movie_repository)],
) -> ParticipantSessionService:
	return ParticipantSessionService(participant_session_repo, pre_shuffled_movies_repo)


def get_participant_service(
	participant_repo: Annotated[ParticipantRepository, Depends(get_participant_repository)],
	study_condition_repo: Annotated[StudyConditionRepository, Depends(get_study_condition_repository)],
	demographics_repo: Annotated[DemographicsRepository, Depends(get_demographics_repository)],
) -> ParticipantService:
	return ParticipantService(participant_repo, study_condition_repo, demographics_repo)


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
	step_repo: Annotated[StudyStepRepository, Depends(get_study_step_repository)],
	condition_repo: Annotated[StudyConditionRepository, Depends(get_study_condition_repository)],
) -> StudyService:
	return StudyService(study_repo, step_repo, condition_repo)


def get_study_step_service(
	step_repo: Annotated[StudyStepRepository, Depends(get_study_step_repository)],
	page_repo: Annotated[PageRepository, Depends(get_page_repository)],
) -> StudyStepService:
	return StudyStepService(step_repo, page_repo)


def get_admin_service(
	shuffled_movie_repo: Annotated[PreShuffledMovieRepository, Depends(get_pre_shuffled_movie_repository)],
) -> AdminService:
	return AdminService(shuffled_movie_repo)
