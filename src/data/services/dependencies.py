from typing import Annotated

from fastapi import Depends

from data.repositories.dependencies import get_survey_construct_repository, get_construct_item_repository
from data.repositories.survey_construct import SurveyConstructRepository
from data.repositories.construct_item import ConstructItemRepository

from .construct_item_service import ConstructItemService
from .survey_construct_service import SurveyConstructService


def get_survey_construct_service(
	construct_repo: Annotated[SurveyConstructRepository, Depends(get_survey_construct_repository)],
) -> SurveyConstructService:
	return SurveyConstructService(construct_repo)


def get_construct_item_service(
	construct_item_repo: Annotated[ConstructItemRepository, Depends(get_construct_item_repository)],
) -> ConstructItemService:
	return ConstructItemService(construct_item_repo)
