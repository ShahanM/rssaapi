"""Movie repository module."""

import uuid
from typing import Any, Optional, Sequence, Union

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rssa_api.data.models.movies import Movie, MovieEmotions
from rssa_api.data.repositories.base_repo import BaseRepository


class MovieRepository(BaseRepository[Movie]):
    """Repository for Movie model.

    Inherits from BaseRepository to provide CRUD operations for Movie model.

    Attributes:
        db: The database session.
        model: The Movie model class.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the MovieRepository.

        Args:
            db: The database session.
        """
        super().__init__(db, Movie)

    async def get_movies_with_emotions(self) -> list[Movie]:
        """Get all movies with their associated emotions.

        Returns:
            A list of Movie instances with their emotions loaded.
        """
        query = select(Movie).join(MovieEmotions)

        db_rows = await self.db.execute(query)

        return list(db_rows.scalars().all())

    async def get_movies_with_emotions_from_ids(self, movie_ids: list[uuid.UUID]) -> list[Movie]:
        """Get movies with their associated emotions by a list of movie IDs.

        Args:
            movie_ids: A list of movie UUIDs.

        Returns:
            A list of Movie instances with their emotions loaded.
        """
        query = select(Movie).join(MovieEmotions).where(Movie.id.in_(movie_ids)).options(selectinload(Movie.emotions))
        db_rows = await self.db.execute(query)

        return list(db_rows.scalars().all())

    async def get_movies_with_details_from_ids(self, movie_ids: list[uuid.UUID]) -> Sequence[Movie]:
        """Get movies with their associated details by a list of movie IDs.

        Args:
            movie_ids: A list of movie UUIDs.

        Returns:
            A list of Movie instances with their details loaded.
        """
        query = (
            select(Movie)
            .options(selectinload(Movie.emotions), selectinload(Movie.recommendations_text))
            .where(Movie.id.in_(movie_ids))
        )

        result = await self.db.execute(query)
        movies = result.scalars().all()
        return movies

    async def get_movie_with_details_by_field(self, field_name: str, field_value: Any) -> Optional[Movie]:
        """Get a movie with its associated details by a specific field.

        Args:
            field_name: The name of the field to filter by.
            field_value: The value of the field to match.

        Returns:
            A Movie instance with its details loaded.
        """
        column_attribute = getattr(self.model, field_name, None)
        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        query = (
            select(Movie)
            .options(selectinload(Movie.recommendations_text), selectinload(Movie.emotions))
            .where(column_attribute == field_value)
        )
        result = await self.db.execute(query)
        return result.scalar()

    async def get_by_exact_field_search(self, field_name: str, field_query: str) -> list[Movie]:
        """Get movies by exact field search.

        Args:
            field_name: The name of the field to search.
            field_query: The exact value to match.

        Returns:
            A list of Movie instances that match the exact field value.
        """
        column_attribute = getattr(self.model, field_name, None)
        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        query = select(Movie).where(func.lower(column_attribute) == field_query)
        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def get_movies_by_fuzzy_field_search(
        self, field_name: str, field_query: str, similarity_threshold: float, limit: int
    ) -> list[Movie]:
        """Get movies by fuzzy field search.

        Args:
            field_name: The name of the field to search.
            field_query: The value to match fuzzily.
            similarity_threshold: The minimum similarity score to consider a match.
            limit: The maximum number of results to return.

        Returns:
            A list of Movie instances that match the fuzzy field value.
        """
        column_attribute = getattr(self.model, field_name, None)
        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        query = (
            select(Movie, func.similarity(column_attribute, field_query).label('similarity'))
            .where(func.similarity(column_attribute, field_query) > similarity_threshold)
            .order_by(func.similarity(column_attribute, field_query).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_movies_by_field_prefix_match(self, field_name: str, field_query: str, limit: int) -> list[Movie]:
        """Get movies by field prefix match.

        Args:
            field_name: The name of the field to search.
            field_query: The prefix value to match.
            limit: The maximum number of results to return.

        Returns:
            A list of Movie instances that match the field prefix.
        """
        column_attribute = self._get_column_attrs(field_name)

        query = select(Movie).where(func.lower(column_attribute).like(f'{field_query}%')).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _get_column_attrs(self, field_name) -> Union[Any, None]:
        column_attribute = getattr(self.model, field_name, None)
        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        return column_attribute

    async def get_movies_with_emotions_by_movielens_ids(self, movielens_ids: list[str]) -> list[Movie]:
        """Get movies with their associated emotions by a list of MovieLens IDs.

        Args:
            movielens_ids: A list of MovieLens IDs.

        Returns:
            A list of Movie instances with their emotions loaded.
        """
        query = (
            select(Movie)
            .options(selectinload(Movie.emotions))
            .join(Movie.emotions)
            .where(
                Movie.movielens_id.in_(movielens_ids),
            )
        )
        db_rows = await self.db.execute(query)

        return list(db_rows.scalars().all())

    async def get_paged_movies(self, limit: int, offset: int, ordering: str = 'none') -> list[Movie]:
        """Get a paged list of movies with optional ordering.

        Args:
            limit: The maximum number of movies to return.
            offset: The number of movies to skip.
            ordering: The ordering criteria ('none', 'popularity', etc.).

        Returns:
            A list of Movie instances.
        """
        query = select(Movie)
        if ordering != 'none':
            query = query.order_by(desc(Movie.count), desc(Movie.year), desc(Movie.ave_rating))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def get_paged_movies_with_details(self, limit: int, offset: int) -> list[Movie]:
        """Get a paged list of movies with their details.

        Args:
            limit: The maximum number of movies to return.
            offset: The number of movies to skip.

        Returns:
            A list of Movie instances with their details loaded.
        """
        query = (
            select(Movie)
            .options(selectinload(Movie.emotions), selectinload(Movie.recommendations_text))
            .order_by(Movie.id)
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def count_movies(self) -> int:
        """Count the total number of movies.

        Returns:
            The total number of movies.
        """
        query = select(func.count()).select_from(Movie)

        result = await self.db.execute(query)

        return result.scalar_one()
