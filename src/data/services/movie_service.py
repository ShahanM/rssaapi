import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.movies import Movie
from data.repositories.movies import MovieRepository


class MovieService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.movie_repo = MovieRepository(db)

	async def get_movies_with_emotions(self) -> List[Movie]:
		movie_with_emotion = await self.movie_repo.get_movies_with_emotions()

		return movie_with_emotion

	async def get_movies_from_ids(self, movie_ids: List[uuid.UUID]) -> Optional[List[Movie]]:
		movie_results = await self.movie_repo.get_all_from_ids(movie_ids)

		return movie_results

	async def get_movies_with_emotions_from_ids(self, movie_ids: List[uuid.UUID]) -> List[Movie]:
		movies_to_send = await self.movie_repo.get_movies_with_emotions_from_ids(movie_ids)

		return movies_to_send
