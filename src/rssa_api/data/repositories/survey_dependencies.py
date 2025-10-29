from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.rssadb import get_db

from .survey_constructs import (
    ConstructItemRepository,
    ConstructScaleRepository,
    ScaleLevelRepository,
    SurveyConstructRepository,
)


def get_survey_construct_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SurveyConstructRepository:
    return SurveyConstructRepository(db)


def get_construct_scale_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConstructScaleRepository:
    return ConstructScaleRepository(db)


def get_construct_item_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConstructItemRepository:
    return ConstructItemRepository(db)


def get_scale_level_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScaleLevelRepository:
    return ScaleLevelRepository(db)
