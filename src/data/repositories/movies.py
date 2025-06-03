import uuid
from typing import List

from pydantic import BaseModel
from sqlalchemy import select
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
		orm_mode = True


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
