import uuid
from typing import Optional, Sequence, Union

from sqlalchemy import Row, Select, and_, asc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from rssa_api.data.models.participant_responses import Feedback
from rssa_api.data.models.study_components import (
    Study,
    StudyCondition,
    StudyStep,
    StudyStepPage,
    StudyStepPageContent,
    User,
)
from rssa_api.data.models.study_components import StudyStepPageContent as PageContent
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.models.survey_constructs import SurveyConstruct, SurveyScale
from rssa_api.data.repositories.base_ordered_repo import BaseOrderedRepository, OrderedRepoQueryOptions
from rssa_api.data.repositories.base_repo import BaseRepository


class StudyRepository(BaseRepository[Study]):
    """Repository for Study model."""

    SEARCHABLE_COLUMNS = ['name', 'description']
    LOAD_FULL_DETAILS = (selectinload(Study.study_steps), selectinload(Study.study_conditions))


class StudyStepRepository(BaseOrderedRepository[StudyStep]):
    """Repository for StudyStep model.

    Attributes:
        parent_id_column_name: Configured the BaseOrderedRepository to use 'study_id' as the parent ID column.
    """

    parent_id_column_name: str = 'study_id'

    async def validate_path_uniqueness(
        self, study_id: uuid.UUID, path: str, exclude_step_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Validate that a StudyStep path is unique within a study, optionally excluding a specific step ID.

        Args:
            study_id: The UUID of the study.
            path: The path to validate.
            exclude_step_id: An optional UUID of a step to exclude from the check.

        Returns:
            True if the path is unique within the study, False otherwise.
        """
        query = select(StudyStep).where(and_(StudyStep.study_id == study_id, StudyStep.path == path))
        if exclude_step_id:
            query = query.where(StudyStep.id != exclude_step_id)

        existing_step = await self.db.execute(query)

        if existing_step.first():
            return False

        return True


class StudyStepPageRepository(BaseOrderedRepository[StudyStepPage]):
    """Repository for StudyStepPage model.

    Attributes:
        parent_id_column_name: Configured the BaseOrderedRepository to use 'study_id' as the parent ID column.
    """

    parent_id_column_name: str = 'study_step_id'

    SEARCHABLE_COLUMNS = ['name', 'description']
    LOAD_FULL_DETAILS = (
        selectinload(StudyStepPage.study_step_page_contents)
        .selectinload(PageContent.survey_construct)
        .selectinload(SurveyConstruct.survey_items),
        selectinload(StudyStepPage.study_step_page_contents).selectinload(PageContent.survey_construct),
        selectinload(StudyStepPage.study_step_page_contents)
        .selectinload(PageContent.survey_scale)
        .selectinload(SurveyScale.survey_scale_levels),
    )


class StudyConditionRepository(BaseRepository[StudyCondition]):
    """Repository for StudyCondition model.

    Attributes:
        db: The database session.
        model: The StudyCondition model class.
    """

    async def get_participant_count_by_condition(self, study_id: uuid.UUID) -> list[Row[tuple[uuid.UUID, str, int]]]:
        """Get participant counts grouped by study conditions for a specific study.

        Args:
            study_id: The UUID of the study.

        Returns:
            A list of rows containing condition ID, condition name, and participant count.
        """
        condition_counts_query = (
            select(
                StudyCondition.id.label('study_condition_id'),
                StudyCondition.name.label('study_condition_name'),
                func.count(StudyParticipant.id).label('participant_count'),
            )
            .join(StudyParticipant, StudyParticipant.study_condition_id == StudyCondition.id, isouter=True)
            .where(StudyCondition.study_id == study_id)
            .group_by(StudyCondition.id, StudyCondition.name)
            .order_by(StudyCondition.name)
        )

        condition_counts_result = await self.db.execute(condition_counts_query)
        condition_counts_rows = condition_counts_result.all()

        return list(condition_counts_rows)


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

    async def get_all_ordered_instances(
        self,
        parent_id: uuid.UUID,
        limit: Optional[int] = None,
        include_deleted: bool = False,
    ) -> Sequence[StudyStepPageContent]:
        """Get all ordered instances for a given parent ID with detailed load options.

        Args:
            parent_id: The parent ID.
            limit: Optional limit on the number of instances to retrieve.
            include_deleted: Whether to include soft-deleted instances.

        Returns:
            A list of ordered instances with relationships loaded.
        """
        options = OrderedRepoQueryOptions(
            filters={self.parent_id_column_name: parent_id},
            sort_by='order_position',
            sort_desc=False,
            limit=limit,
            include_deleted=include_deleted,
            load_options=self.DETAILED_LOAD_OPTIONS,
        )
        return await self.find_many(options)


class FeedbackRepository(BaseRepository[Feedback]):
    """Repository for managing Feedback entities in the database.

    Inherits from BaseRepository to provide CRUD operations for Feedback model.
    """

    pass
