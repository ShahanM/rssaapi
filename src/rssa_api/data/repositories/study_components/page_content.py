"""Repository for managing PageContent entities in the database."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rssa_api.data.models.study_components import PageContent
from rssa_api.data.models.survey_constructs import ConstructScale, SurveyConstruct
from rssa_api.data.repositories.base_ordered_repo import BaseOrderedRepository


class PageContentRepository(BaseOrderedRepository[PageContent]):
    """Repository for PageContent model.

    Attributes:
        db: The database session.
        model: The PageContent model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the PageContentRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, PageContent, parent_id_column_name='page_id')

    async def get_detailed_content_by_page_id(self, page_id: uuid.UUID) -> Sequence[PageContent]:
        """Get all PageContent entries for a specific page, with related survey constructs and scales eagerly loaded.

        Args:
            page_id: The UUID of the page.

        Returns:
            A sequence of PageContent instances with related details.
        """
        query = (
            select(PageContent)
            .options(
                selectinload(PageContent.survey_construct).selectinload(SurveyConstruct.items),
                selectinload(PageContent.construct_scale).selectinload(ConstructScale.scale_levels),
            )
            .where(PageContent.page_id == page_id)
            .order_by(PageContent.order_position.asc())
        )

        result = await self.db.execute(query)

        return result.scalars().all()
