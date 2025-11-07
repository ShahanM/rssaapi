"""Repository for SurveyConstruct and related models."""

import uuid
from typing import Optional

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rssa_api.data.models.survey_constructs import ConstructItem, ConstructScale, ScaleLevel, SurveyConstruct
from rssa_api.data.repositories.base_ordered_repo import BaseOrderedRepository
from rssa_api.data.repositories.base_repo import BaseRepository


class SurveyConstructRepository(BaseRepository[SurveyConstruct]):
    """Repository for SurveyConstruct model.

    Attributes:
        db: The database session.
        model: The SurveyConstruct model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the SurveyConstructRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, SurveyConstruct)

    async def get_constructs_paginated(
        self,
        limit: int,
        offset: int,
        sort_by: Optional[str],
        sort_dir: Optional[str],
        search: Optional[str],
    ) -> list[Row]:
        """Get paginated survey constructs with optional sorting and searching.

        Args:
            limit: The maximum number of constructs to return.
            offset: The number of constructs to skip.
            sort_by: The column to sort by.
            sort_dir: The direction of sorting ('asc' or 'desc').
            search: A search string to filter constructs by name or description.

        Returns:
            A list of rows containing construct details.
        """
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

    async def get_detailed_construct_object(self, construct_id: uuid.UUID) -> Optional[SurveyConstruct]:
        """Get a SurveyConstruct with its associated ConstructItems.

        Args:
            construct_id: The UUID of the survey construct.

        Returns:
            The SurveyConstruct instance with its items loaded.
        """
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
        """Count total survey constructs with optional searching.

        Args:
            search: A search string to filter constructs by name or description.

        Returns:
            The total number of survey constructs.
        """
        query = select(func.count()).select_from(SurveyConstruct)
        query = self._add_search_filter(query, search, ['name', 'description'])
        result = await self.db.execute(query)
        return result.scalar_one()


class ConstructScaleRepository(BaseRepository[ConstructScale]):
    """Repository for ConstructScale model."""

    def __init__(self, db: AsyncSession):
        """Initialize the ConstructScaleRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, ConstructScale)

    async def get_details(self, scale_id: uuid.UUID) -> Optional[ConstructScale]:
        """Get a ConstructScale with its associated ScaleLevels.

        Args:
            scale_id: The UUID of the construct scale.

        Returns:
            The ConstructScale instance with its scale levels loaded.
        """
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
        """Get paginated construct scales with optional sorting and searching.

        Args:
            limit: The maximum number of scales to return.
            offset: The number of scales to skip.
            sort_by: The column to sort by.
            sort_dir: The direction of sorting ('asc' or 'desc').
            search: A search string to filter scales by name or description.

        Returns:
            A list of rows containing construct scale details.
        """
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
        """Count total construct scales with optional searching.

        Args:
            search: A search string to filter scales by name or description.

        Returns:
            The total number of construct scales.
        """
        query = select(func.count()).select_from(ConstructScale)
        query = self._add_search_filter(query, search, ['name', 'description'])
        result = await self.db.execute(query)
        return result.scalar_one()


class ConstructItemRepository(BaseOrderedRepository[ConstructItem]):
    """Repository for ConstructItem model."""

    def __init__(self, db: AsyncSession):
        """Initialize the ConstructItemRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, ConstructItem, parent_id_column_name='construct_id')


class ScaleLevelRepository(BaseOrderedRepository[ScaleLevel]):
    """Repository for ScaleLevel model."""

    def __init__(self, db: AsyncSession):
        """Initialize the ScaleLevelRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, ScaleLevel, parent_id_column_name='scale_id')
