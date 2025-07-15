import uuid
from typing import List, Optional

from data.models.movies import Movie
from data.repositories import MovieRepository


class MovieService:
	def __init__(self, movie_repo: MovieRepository):
		self.movie_repo = movie_repo

	async def get_movies_with_emotions(self) -> List[Movie]:
		movie_with_emotion = await self.movie_repo.get_movies_with_emotions()

		return movie_with_emotion

	async def get_movies_from_ids(self, movie_ids: List[uuid.UUID]) -> Optional[List[Movie]]:
		movie_results = await self.movie_repo.get_all_from_ids(movie_ids)

		return movie_results

	async def get_movies_with_emotions_from_ids(self, movie_ids: List[uuid.UUID]) -> List[Movie]:
		movies_to_send = await self.movie_repo.get_movies_with_emotions_from_ids(movie_ids)

		return movies_to_send

	async def get_movies_by_movielens_ids(self, movielens_ids: List[str]) -> List[Movie]:
		movies_to_send = await self.movie_repo.get_all_by_field_in_values('movielens_id', movielens_ids)

		return movies_to_send

	async def get_movie_by_movielens_id(self, movielens_id: str) -> Movie:
		return await self.movie_repo.get_by_field('movielens_id', movielens_id)

	async def get_movie_by_exact_title_search(self, title_query: str) -> List[Movie]:
		return await self.movie_repo.get_by_exact_field_search('title', title_query)

	async def get_movies_by_fuzzy_title_match(self, query: str, similarity_threshold: float, limit: int) -> List[Movie]:
		return await self.movie_repo.get_movies_by_fuzzy_field_search('title', query, similarity_threshold, limit)

	async def get_movies_by_title_prefix_match(self, query: str, limit: int) -> List[Movie]:
		return await self.movie_repo.get_movies_by_field_prefix_match('title', query, limit)

	async def get_movies_with_emotions_by_movielens_ids(self, movielens_ids: List[str]) -> List[Movie]:
		return await self.movie_repo.get_movies_with_emotions_by_movielens_ids(movielens_ids)
