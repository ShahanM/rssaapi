import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models.study_components import PageContent
from data.models.survey_constructs import ConstructScale, SurveyConstruct
from data.repositories.base_ordered_repo import BaseOrderedRepository


class PageContentRepository(BaseOrderedRepository[PageContent]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PageContent, parent_id_column_name='page_id')

    async def get_detailed_content_by_page_id(self, page_id: uuid.UUID) -> Sequence[PageContent]:
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
