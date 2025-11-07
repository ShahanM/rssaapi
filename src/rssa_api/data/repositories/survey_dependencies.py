"""Survey Dependencies Repository."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.rssadb import get_db

from .survey_constructs.survey_constructs import (
    ConstructItemRepository,
    ConstructScaleRepository,
    ScaleLevelRepository,
    SurveyConstructRepository,
)


def get_survey_construct_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SurveyConstructRepository:
    """Get SurveyConstructRepository dependency."""
    return SurveyConstructRepository(db)


def get_construct_scale_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConstructScaleRepository:
    """Get ConstructScaleRepository dependency."""
    return ConstructScaleRepository(db)


def get_construct_item_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConstructItemRepository:
    """Get ConstructItemRepository dependency."""
    return ConstructItemRepository(db)


def get_scale_level_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScaleLevelRepository:
    """Get ScaleLevelRepository dependency."""
    return ScaleLevelRepository(db)
