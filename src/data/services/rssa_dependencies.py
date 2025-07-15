from typing import Annotated

from fastapi import Depends

from data.repositories import (
	ConstructItemRepository,
	DemographicsRepository,
	ParticipantMovieSessionRepository,
	ParticipantRepository,
	PreShuffledMovieRepository,
	StudyConditionRepository,
	StudyRepository,
	SurveyConstructRepository,
)
from data.repositories.rssa_dependencies import (
	get_construct_item_repository,
	get_demographics_repository,
	get_participant_repository,
	get_participant_session_repository,
	get_pre_shuffled_movie_repository,
	get_study_condition_repository,
	get_study_repository,
	get_survey_construct_repository,
)

from .construct_item_service import ConstructItemService
from .participant_service import ParticipantService
from .participant_session_service import ParticipantSessionService
from .study_condition_service import StudyConditionService
from .survey_construct_service import SurveyConstructService


def get_survey_construct_service(
	construct_repo: Annotated[SurveyConstructRepository, Depends(get_survey_construct_repository)],
) -> SurveyConstructService:
	return SurveyConstructService(construct_repo)


def get_construct_item_service(
	construct_item_repo: Annotated[ConstructItemRepository, Depends(get_construct_item_repository)],
) -> ConstructItemService:
	return ConstructItemService(construct_item_repo)


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
