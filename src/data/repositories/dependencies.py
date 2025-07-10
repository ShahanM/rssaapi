from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db

from .construct_item import ConstructItemRepository
from .survey_construct import SurveyConstructRepository


def get_survey_construct_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> SurveyConstructRepository:
	return SurveyConstructRepository(db)


def get_construct_item_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> ConstructItemRepository:
	return ConstructItemRepository(db)
