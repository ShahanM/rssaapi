from typing import Annotated

from fastapi import Depends

from rssa_api.data.repositories import (
    ConstructItemRepository,
    ConstructScaleRepository,
    ScaleLevelRepository,
    SurveyConstructRepository,
)
from rssa_api.data.repositories.survey_dependencies import (
    get_construct_item_repository,
    get_construct_scale_repository,
    get_scale_level_repository,
    get_survey_construct_repository,
)

from .construct_items import ConstructItemService
from .construct_scales import ConstructScaleService
from .scale_levels import ScaleLevelService
from .survey_constructs import SurveyConstructService


def get_survey_construct_service(
    construct_repo: Annotated[SurveyConstructRepository, Depends(get_survey_construct_repository)],
    item_repo: Annotated[ConstructItemRepository, Depends(get_construct_item_repository)],
) -> SurveyConstructService:
    return SurveyConstructService(construct_repo, item_repo)


def get_construct_scale_service(
    construct_scale_repo: Annotated[ConstructScaleRepository, Depends(get_construct_scale_repository)],
    scale_level_repo: Annotated[ScaleLevelRepository, Depends(get_scale_level_repository)],
) -> ConstructScaleService:
    return ConstructScaleService(construct_scale_repo, scale_level_repo)


def get_construct_item_service(
    item_repo: Annotated[ConstructItemRepository, Depends(get_construct_item_repository)],
) -> ConstructItemService:
    return ConstructItemService(item_repo)


def get_scale_level_service(
    scale_level_repo: Annotated[ScaleLevelRepository, Depends(get_scale_level_repository)],
) -> ScaleLevelService:
    return ScaleLevelService(scale_level_repo)
