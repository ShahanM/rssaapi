"""Component Dependencies Repository.

Provides dependency injection functions for study component repositories.

"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.rssadb import get_db

from .study_components.page_content import PageContentRepository
from .study_components.step_page import StepPageRepository
from .study_components.study import StudyRepository
from .study_components.study_condition import StudyConditionRepository
from .study_components.study_step import StudyStepRepository


def get_study_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyRepository:
    """Get StudyRepository dependency."""
    return StudyRepository(db)


def get_study_condition_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyConditionRepository:
    """Get StudyConditionRepository dependency."""
    return StudyConditionRepository(db)


def get_page_content_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PageContentRepository:
    """Get PageContentRepository dependency."""
    return PageContentRepository(db)


def get_step_page_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StepPageRepository:
    """Get StepPageRepository dependency."""
    return StepPageRepository(db)


def get_study_step_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyStepRepository:
    """Get StudyStepRepository dependency."""
    return StudyStepRepository(db)
