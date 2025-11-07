"""Repository for managing StepPage entities in the database."""

import uuid
from typing import Optional

from sqlalchemy import and_, asc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rssa_api.data.models.study_components import PageContent, StepPage
from rssa_api.data.models.survey_constructs import ConstructScale, SurveyConstruct

from ..base_ordered_repo import BaseOrderedRepository


class StepPageRepository(BaseOrderedRepository[StepPage]):
    """Repository for StepPage model.

    Attributes:
        db: The database session.
        model: The StepPage model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the StepPageRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, StepPage, parent_id_column_name='step_id')

    async def get_pages_by_step_id(self, step_id: uuid.UUID) -> list[StepPage]:
        """Get all pages associated with a specific step, ordered by their position.

        Args:
            step_id: The UUID of the step.

        Returns:
            A list of StepPage instances ordered by order_position.
        """
        query = select(StepPage).where(StepPage.step_id == step_id).order_by(asc(StepPage.order_position))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_page_order_position(self, page_id: uuid.UUID, step_id: uuid.UUID) -> Optional[int]:
        """Fetches only the order_position of a specific page within a step.

        Args:
            page_id: The UUID of the page.
            step_id: The UUID of the step.

        Returns:
            The order_position of the page if found, else None.
        """
        query = (
            select(StepPage.order_position).where(StepPage.id == page_id).where(StepPage.step_id == step_id).limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_page_with_full_details(self, page_id: uuid.UUID) -> Optional[StepPage]:
        """Fetched a Page object along with its associated PageContent and their respective SurveyConstruct details.

        Args:
            page_id: The UUID of the page.

        Returns:
            The StepPage instance with full details or None if not found.
        """
        query = (
            select(StepPage)
            .where(StepPage.id == page_id)
            .options(
                selectinload(StepPage.page_contents)
                .selectinload(PageContent.survey_construct)
                .selectinload(SurveyConstruct.items)
            )
        )
        result = await self.db.execute(query)
        page_instance = result.scalar_one_or_none()
        return page_instance

    async def get_first_page_in_step(self, step_id: uuid.UUID) -> Optional[StepPage]:
        """Fetches the first page within a step based on order_position, with all its related details eagerly loaded.

        Args:
            step_id: The UUID of the step.

        Returns:
            The first StepPage instance with full details or None if not found.
        """
        query = (
            select(StepPage)
            .where(StepPage.step_id == step_id)
            .order_by(StepPage.order_position.asc())
            .limit(1)
            .options(
                selectinload(StepPage.page_contents)
                .selectinload(PageContent.survey_construct)
                .selectinload(SurveyConstruct.items),
                selectinload(StepPage.page_contents)
                .selectinload(PageContent.construct_scale)
                .selectinload(ConstructScale.scale_levels),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_page_by_step_next_order(self, step_id: uuid.UUID, current_order_position: int) -> Optional[StepPage]:
        """Fetches the next page within a step based on order_position, with all its related details eagerly loaded.

        Args:
            step_id: The UUID of the step.
            current_order_position: The current order position of the page.

        Returns:
            The next StepPage instance with full details or None if not found.
        """
        query = (
            select(StepPage)
            .where(StepPage.step_id == step_id)
            .where(StepPage.order_position > current_order_position)
            .order_by(StepPage.order_position.asc())
            .limit(1)
            .options(
                selectinload(StepPage.page_contents)
                .selectinload(PageContent.survey_construct)
                .selectinload(SurveyConstruct.items),
                selectinload(StepPage.page_contents)
                .selectinload(PageContent.survey_construct)
                .selectinload(ConstructScale.scale_levels),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_page_with_content_detail(self, page_id: uuid.UUID) -> Optional[StepPage]:
        """Fetches a Page object along with its associated PageContent.

        The PageContent's SurveyConstruct and ConstructScale details are eagerly loaded.

        Args:
            page_id: The UUID of the page.

        Returns:
            The StepPage instance with its PageContent or None if not found.
        """
        query = (
            select(StepPage)
            .where(StepPage.id == page_id)
            .order_by(StepPage.order_position.asc())
            .options(
                selectinload(StepPage.page_contents)
                .selectinload(PageContent.survey_construct)
                .selectinload(SurveyConstruct.items),
                selectinload(StepPage.page_contents).selectinload(PageContent.survey_construct),
                selectinload(StepPage.page_contents)
                .selectinload(PageContent.construct_scale)
                .selectinload(ConstructScale.scale_levels),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def has_subsequent_page(self, step_id: uuid.UUID, current_order_position: int) -> bool:
        """Checks if there is any page with a higher order_position in the given step.

        This is used to determine if a page is the 'last_page'.

        Args:
            step_id: The UUID of the step.
            current_order_position: The current order position of the page.
        """
        stmt = (
            select(StepPage.id)
            .where(and_(StepPage.step_id == step_id, StepPage.order_position > current_order_position))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def get_last_page_in_step(self, step_id: uuid.UUID) -> Optional[StepPage]:
        """Fetches the last page within a step based on order_position.

        Args:
            step_id: The UUID of the step.

        Returns:
            The last StepPage instance or None if not found.
        """
        query = select(StepPage).where(StepPage.study_id == step_id).order_by(StepPage.order_position.desc())
        result = await self.db.execute(query)
        step = result.scalars().first()

        return step
