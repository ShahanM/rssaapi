from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db

from .demographics import DemographicsRepository
from .page import PageRepository
from .page_content import PageContentRepository
from .participant import ParticipantRepository
from .participant_movie_session import ParticipantMovieSessionRepository
from .pre_shuffled_movie_list import PreShuffledMovieRepository
from .study import StudyRepository
from .study_condition import StudyConditionRepository
from .study_step import StudyStepRepository


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
