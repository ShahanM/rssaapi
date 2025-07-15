from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db

from .construct_item import ConstructItemRepository
from .demographics import DemographicsRepository
from .participant import ParticipantRepository
from .participant_movie_session import ParticipantMovieSessionRepository
from .pre_shuffled_movie_list import PreShuffledMovieRepository
from .study import StudyRepository
from .study_condition import StudyConditionRepository
from .survey_construct import SurveyConstructRepository


def get_survey_construct_repository(
	db: Annotated[AsyncSession, Depends(get_db)],
) -> SurveyConstructRepository:
	return SurveyConstructRepository(db)


def get_construct_item_repository(
	db: Annotated[AsyncSession, Depends(get_db)],
) -> ConstructItemRepository:
	return ConstructItemRepository(db)


def get_study_repository(
	db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyRepository:
	return StudyRepository(db)


def get_study_condition_repository(
	db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyConditionRepository:
	return StudyConditionRepository(db)


def get_participant_session_repository(
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
