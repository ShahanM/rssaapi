"""Service layer for survey constructs, items, scales, and scale levels."""

from rssa_api.data.models.survey_constructs import SurveyConstruct, SurveyItem, SurveyScale, SurveyScaleLevel
from rssa_api.data.repositories.survey_components import (
    SurveyConstructRepository,
    SurveyItemRepository,
    SurveyScaleLevelRepository,
    SurveyScaleRepository,
)
from rssa_api.data.services.base_ordered_service import BaseOrderedService
from rssa_api.data.services.base_service import BaseService


class SurveyConstructService(BaseService[SurveyConstruct, SurveyConstructRepository]):
    """Service for managing survey constructs.

    This service provides methods to create, retrieve, update, and delete survey constructs,
    as well as to manage construct items and their order.
    """

    pass


class SurveyItemService(BaseOrderedService[SurveyItem, SurveyItemRepository]):
    """Service for managing survey construct items."""

    pass


class SurveyScaleService(BaseService[SurveyScale, SurveyScaleRepository]):
    """Service for managing survey scales."""

    pass


class SurveyScaleLevelService(BaseOrderedService[SurveyScaleLevel, SurveyScaleLevelRepository]):
    """Service for managing survey scale levels."""

    pass
