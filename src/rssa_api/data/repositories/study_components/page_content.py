"""Repository for managing PageContent entities in the database."""

from sqlalchemy.orm import selectinload

from rssa_api.data.models.study_components import StudyStepPageContent
from rssa_api.data.models.survey_constructs import SurveyConstruct, SurveyScale
from rssa_api.data.repositories.base_ordered_repo import BaseOrderedRepository


class StudyStepPageContentRepository(BaseOrderedRepository[StudyStepPageContent]):
    """Repository for PageContent model.

    Attributes:
        parent_id_column_name: Configured the BaseOrderedRepository to use 'study_step_page_id' as the parent ID column.
    """

    parent_id_column_name: str = 'study_step_page_id'

    DETAILED_LOAD_OPTIONS = (
        selectinload(StudyStepPageContent.survey_construct).selectinload(SurveyConstruct.survey_items),
        selectinload(StudyStepPageContent.survey_scale).selectinload(SurveyScale.survey_scale_levels),
    )
