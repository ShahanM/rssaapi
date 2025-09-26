import uuid
from typing import Optional

from async_lru import alru_cache

from data.models.movies import Movie
from data.repositories import MovieRepository
from data.schemas.movie_schemas import MovieDetailSchema


class MovieService:
    def __init__(self, movie_repo: MovieRepository):
        self.movie_repo = movie_repo

    async def get_movies_with_emotions(self) -> list[Movie]:
        return await self.movie_repo.get_movies_with_emotions()

    async def get_movies_from_ids(self, movie_ids: list[uuid.UUID]) -> list[MovieDetailSchema]:
        movies = await self.movie_repo.get_movies_with_details_from_ids(movie_ids)
        if not movies:
            return []
        return [MovieDetailSchema.model_validate(movie) for movie in movies]

    async def get_movies_with_emotions_from_ids(self, movie_ids: list[uuid.UUID]) -> list[Movie]:
        return await self.movie_repo.get_movies_with_emotions_from_ids(movie_ids)

    async def get_movies_by_movielens_ids(self, movielens_ids: list[str]) -> list[Movie]:
        return await self.movie_repo.get_all_by_field_in_values('movielens_id', movielens_ids)

    async def get_movie_by_movielens_id(self, movielens_id: str) -> Movie:
        return await self.movie_repo.get_by_field('movielens_id', movielens_id)

    async def get_movie_details_by_movielens_id(self, movielens_id: str) -> MovieDetailSchema:
        movie = await self.movie_repo.get_movie_with_details_by_field('movielens_id', movielens_id)
        return MovieDetailSchema.model_validate(movie)

    async def get_movie_by_imdb_id(self, imdb_id: str) -> Optional[Movie]:
        parsed_id = imdb_id[2:] if imdb_id[:2].lower() == 'tt' else imdb_id
        return await self.movie_repo.get_by_field('imdb_id', parsed_id)

    async def get_movie_by_exact_title_search(self, title_query: str) -> list[Movie]:
        return await self.movie_repo.get_by_exact_field_search('title', title_query)

    async def get_movies_by_fuzzy_title_match(self, query: str, similarity_threshold: float, limit: int) -> list[Movie]:
        return await self.movie_repo.get_movies_by_fuzzy_field_search('title', query, similarity_threshold, limit)

    async def get_movies_by_title_prefix_match(self, query: str, limit: int) -> list[Movie]:
        return await self.movie_repo.get_movies_by_field_prefix_match('title', query, limit)

    async def get_movies_with_emotions_by_movielens_ids(self, movielens_ids: list[str]) -> list[Movie]:
        return await self.movie_repo.get_movies_with_emotions_by_movielens_ids(movielens_ids)

    @alru_cache(maxsize=128)
    async def get_movies(self, limit: int, offset: int) -> list[Movie]:
        return await self.movie_repo.get_paged_movies(limit, offset)

    @alru_cache(maxsize=128)
    async def get_movies_with_details(self, limit: int, offset: int) -> list[Movie]:
        return await self.movie_repo.get_paged_movies_with_details(limit, offset)

    @alru_cache(maxsize=1)
    async def get_movie_count(self) -> int:
        return await self.movie_repo.count_movies()
