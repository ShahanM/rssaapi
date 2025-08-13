import uuid
from typing import Any, List, Union

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models.movies import Movie, MovieEmotions
from data.repositories.base_repo import BaseRepository


class MovieRecommendationSchema(BaseModel):
	id: uuid.UUID
	movie_id: uuid.UUID
	formal: str
	informal: str
	source: str
	model: str

	class Config:
		from_attributes = True


class MovieRepository(BaseRepository[Movie]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, Movie)

	async def get_movies_with_emotions(self) -> List[Movie]:
		query = select(Movie).join(MovieEmotions)

		db_rows = await self.db.execute(query)

		return list(db_rows.scalars().all())

	async def get_movies_with_emotions_from_ids(self, movie_ids: List[uuid.UUID]) -> List[Movie]:
		query = select(Movie).join(MovieEmotions).where(Movie.id.in_(movie_ids)).options(selectinload(Movie.emotions))
		db_rows = await self.db.execute(query)

		return list(db_rows.scalars().all())

	async def get_by_exact_field_search(self, field_name: str, field_query: str) -> List[Movie]:
		column_attribute = getattr(self.model, field_name, None)
		if column_attribute is None:
			raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

		query = select(Movie).where(func.lower(column_attribute) == field_query)
		result = await self.db.execute(query)

		return list(result.scalars().all())

	async def get_movies_by_fuzzy_field_search(
		self, field_name: str, field_query: str, similarity_threshold: float, limit: int
	) -> List[Movie]:
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

	async def get_movies_by_field_prefix_match(self, field_name: str, field_query: str, limit: int) -> List[Movie]:
		column_attribute = self._get_column_attrs(field_name)

		query = select(Movie).where(func.lower(column_attribute).like(f'{field_query}%')).limit(limit)

		result = await self.db.execute(query)
		return list(result.scalars().all())

	def _get_column_attrs(self, field_name) -> Union[Any, None]:
		column_attribute = getattr(self.model, field_name, None)
		if column_attribute is None:
			raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

		return column_attribute

	async def get_movies_with_emotions_by_movielens_ids(self, movielens_ids: List[str]) -> List[Movie]:
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
