"""Repository for managing Study entities in the database."""

import uuid
from typing import Optional, Union

from sqlalchemy import Row, Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from rssa_api.data.models.study_components import Study, User
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.repositories.base_repo import BaseRepository


class StudyRepository(BaseRepository[Study]):
    """Repository for Study model.

    Attributes:
        db: The database session.
        model: The Study model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the StudyRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, Study)

    async def get_detailed_study_object(
        self,
        user_id: Optional[uuid.UUID],
        study_id: uuid.UUID,
    ) -> Optional[Row]:
        """Get a detailed Study object by its ID, including owner and creator info.

        Args:
            user_id: The UUID of the user requesting the study (for access control).
            study_id: The UUID of the study.

        Returns:
            A Row containing the Study instance and related owner/creator info if found, else None.
        """
        Owner = aliased(User, name='owner')
        Creator = aliased(User, name='creator')

        query = (
            select(
                Study,
                Owner.auth0_sub.label('owner_auth0_sub'),
                Creator.auth0_sub.label('creator_auth0_sub'),
            )
            .join_from(Study, Owner, Study.owner_id == Owner.id, isouter=True)
            .join_from(Study, Creator, Study.created_by_id == Creator.id, isouter=True)
            .options(
                selectinload(Study.steps),
                selectinload(Study.conditions),
            )
            .where(Study.id == study_id)
        )
        query = self._add_user_filter(query, user_id)

        result = await self.db.execute(query)

        return result.one_or_none()

    async def get_studies_paginated(
        self,
        user_id: Optional[uuid.UUID],
        limit: int,
        offset: int,
        sort_by: Optional[str],
        sort_dir: Optional[str],
        search: Optional[str],
    ) -> list[Row]:
        """Get a paginated list of studies with optional filtering and sorting.

        Args:
            user_id: The UUID of the user requesting the studies (for access control).
            limit: The maximum number of studies to return.
            offset: The number of studies to skip.
            sort_by: The column to sort by.
            sort_dir: The direction to sort (asc or desc).
            search: A search string to filter studies by name or description.

        Returns:
            A list of Rows containing Study instances.
        """
        query = select(Study.id, Study.name, Study.created_at, Study.updated_at, Study.created_by_id)

        query = self._add_user_filter(query, user_id)
        query = self._add_search_filter(query, search, ['name', 'description'])
        query = self._sort_by_column(query, sort_by, sort_dir)
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)

        return result.all()  # type: ignore

    async def count_studies(self, user_id: Optional[uuid.UUID], search: Union[str, None]) -> int:
        """Count the total number of studies with optional filtering.

        Args:
            user_id: The UUID of the user requesting the count (for access control).
            search: A search string to filter studies by name or description.

        Returns:
            The total count of studies.
        """
        query = select(func.count()).select_from(Study)
        query = self._add_user_filter(query, user_id)
        query = self._add_search_filter(query, search, ['name', 'description'])
        result = await self.db.execute(query)

        return result.scalar_one()

    async def get_total_participants(
        self,
        study_id: uuid.UUID,
    ) -> Optional[Row]:
        """Get the total number of participants for a specific study, along with owner and creator info.

        Args:
            study_id: The UUID of the study.

        Returns:
            A Row containing the Study instance, total participant count, and related owner/creator info if found,
            else None.
        """
        Owner = aliased(User, name='owner')
        Creator = aliased(User, name='creator')

        query = (
            select(
                Study,
                func.count(StudyParticipant.id).label('total_participants'),
                Owner.auth0_sub.label('owner_auth0_sub'),
                Creator.auth0_sub.label('creator_auth0_sub'),
            )
            .join_from(Study, StudyParticipant, isouter=True)
            .join_from(Study, Owner, Study.owner_id == Owner.id, isouter=True)
            .join_from(Study, Creator, Study.created_by_id == Creator.id, isouter=True)
            .where(Study.id == study_id)
        )

        query = query.group_by(Study.id, Owner.auth0_sub, Creator.auth0_sub)

        study_result = await self.db.execute(query)
        return study_result.first()

    def _add_user_filter(self, query: Select, user_id: Union[uuid.UUID, None]) -> Select:
        if user_id:
            return query.where(or_(Study.owner_id == user_id, Study.created_by_id == user_id))
        return query
