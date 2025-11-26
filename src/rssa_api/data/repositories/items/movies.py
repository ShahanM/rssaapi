"""Movie repository module."""

from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from rssa_api.data.models.movies import Movie
from rssa_api.data.repositories.base_repo import BaseRepository


class MovieRepository(BaseRepository[Movie]):
    """Repository for Movie model.

    Inherits from BaseRepository to provide CRUD operations for Movie model.
    """

    LOAD_EMOTIONS = (selectinload(Movie.emotions),)

    LOAD_FULL_DETAILS = (
        selectinload(Movie.emotions),
        selectinload(Movie.recommendations_text),
    )

    async def get_by_similarity(
        self, field_name: str, query_str: str, threshold: float = 0.3, limit: int = 10
    ) -> Sequence[Movie]:
        """Get movies by fuzzy similarity search (Postgres pg_trgm)."""
        column = self._get_column(field_name)

        similarity = func.similarity(column, query_str)

        query = select(Movie).where(similarity > threshold).order_by(similarity.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_prefix(self, field_name: str, prefix: str, limit: int = 10) -> Sequence[Movie]:
        """Get movies where a specific field starts with the prefix."""
        column = self._get_column(field_name)

        query = select(Movie).where(func.lower(column).like(f'{prefix.lower()}%')).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    def _get_column(self, field_name: str) -> Any:
        attr = getattr(self.model, field_name, None)
        if attr is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        return attr
