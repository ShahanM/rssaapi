import uuid
from operator import attrgetter
from typing import Optional, Union

from sqlalchemy import Row, Select, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models.survey_constructs import ConstructItem, ConstructScale, ScaleLevel, SurveyConstruct
from data.repositories.base_ordered_repo import BaseOrderedRepository
from data.repositories.base_repo import BaseRepository


class SurveyConstructRepository(BaseRepository[SurveyConstruct]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SurveyConstruct)

    async def get_constructs_paginated(
        self,
        limit: int,
        offset: int,
        sort_by: Optional[str],
        sort_dir: Optional[str],
        search: Optional[str],
    ) -> list[Row]:
        query = select(
            SurveyConstruct.id,
            SurveyConstruct.name,
            SurveyConstruct.created_at,
            SurveyConstruct.updated_at,
            SurveyConstruct.created_by_id,
        )

        if sort_by:
            column_to_sort = getattr(SurveyConstruct, sort_by, None)
            if column_to_sort is not None:
                if sort_dir and sort_dir.lower() == 'desc':
                    query.order_by(column_to_sort.desc())
                else:
                    query.order_by(column_to_sort.asc())

        query = self._add_search_filter(query, search, ['name', 'description'])
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)

        return result.all()  # type: ignore

    async def get_detailed_construct_object(self, construct_id: uuid.UUID) -> SurveyConstruct:
        query = (
            select(SurveyConstruct)
            .where(SurveyConstruct.id == construct_id)
            .options(
                selectinload(SurveyConstruct.items),
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_total_constructs(self, search: Optional[str]) -> int:
        query = select(func.count()).select_from(SurveyConstruct)
        query = self._add_search_filter(query, search, ['name', 'description'])
        result = await self.db.execute(query)
        return result.scalar_one()


class ConstructScaleRepository(BaseRepository[ConstructScale]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ConstructScale)

    async def get_details(self, scale_id: uuid.UUID) -> ConstructScale:
        query = (
            select(ConstructScale)
            .where(ConstructScale.id == scale_id)
            .options(selectinload(ConstructScale.scale_levels))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_scales_paginated(
        self,
        limit: int,
        offset: int,
        sort_by: Optional[str],
        sort_dir: Optional[str],
        search: Optional[str],
    ) -> list[Row]:
        query = select(
            ConstructScale.id,
            ConstructScale.name,
            ConstructScale.created_at,
            ConstructScale.updated_at,
            ConstructScale.created_by_id,
        )

        query = self._add_search_filter(query, search, ['name', 'dscription'])
        query = self._sort_by_column(query, sort_by, sort_dir)
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return result.all()  # type: ignore

    async def count_total_scales(self, search: Optional[str]) -> int:
        query = select(func.count()).select_from(ConstructScale)
        query = self._add_search_filter(query, search, ['name', 'description'])
        result = await self.db.execute(query)
        return result.scalar_one()


class ConstructItemRepository(BaseOrderedRepository[ConstructItem]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ConstructItem, parent_id_column_name='construct_id')


class ScaleLevelRepository(BaseOrderedRepository[ScaleLevel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ScaleLevel, parent_id_column_name='scale_id')
