import uuid
from collections.abc import Sequence
from typing import Any, Optional, Union

from async_lru import alru_cache
from rssa_storage.moviedb.models.movies import Movie
from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.shared import RepoQueryOptions

from rssa_api.data.schemas.movie_schemas import MovieDetailSchema, MovieSchema
from rssa_api.data.services.base_service import BaseService


class MovieService(BaseService[Movie, MovieRepository]):
    def __init__(self, movie_repo: MovieRepository):
        self.movie_repo = movie_repo

    async def get_movies_with_emotions(self) -> list[Movie]:
        # return await self.movie_repo.get_all(options=MovieRepository.LOAD_EMOTIONS)
        movies = await self.movie_repo.find_many(RepoQueryOptions(load_options=MovieRepository.LOAD_ALL))
        return list(movies)

    async def get_movies_from_ids(self, movie_ids: list[uuid.UUID]) -> list[MovieDetailSchema]:
        movies = await self.movie_repo.find_many(RepoQueryOptions(ids=movie_ids, load_options=MovieRepository.LOAD_ALL))
        if not movies:
            return []
        return [MovieDetailSchema.model_validate(movie) for movie in movies]

    async def get_movies_with_emotions_from_ids(self, movie_ids: list[uuid.UUID]) -> list[Movie]:
        movies = await self.movie_repo.find_many(
            RepoQueryOptions(ids=movie_ids, load_options=MovieRepository.LOAD_EMOTIONS)
        )
        if not movies:
            return []
        return list(movies)

    async def get_movies_by_movielens_ids(self, movielens_ids: list[str | int]) -> list[Movie]:
        movies = await self.movie_repo.find_many(RepoQueryOptions(filters={'movielens_id': movielens_ids}))
        return list(movies)

    async def get_movie_by_movielens_id(self, movielens_id: str) -> Optional[Movie]:
        return await self.movie_repo.find_one(RepoQueryOptions(filters={'movielens_id': movielens_id}))

    async def get_movie_details_by_movielens_id(self, movielens_id: str) -> MovieDetailSchema:
        movie = await self.movie_repo.find_one(
            RepoQueryOptions(filters={'movielens_id': movielens_id}, load_options=MovieRepository.LOAD_ALL)
        )
        return MovieDetailSchema.model_validate(movie)

    async def get_movie_by_imdb_id(self, imdb_id: str) -> Optional[Movie]:
        parsed_id = imdb_id[2:] if imdb_id[:2].lower() == 'tt' else imdb_id

        return await self.movie_repo.find_one(RepoQueryOptions(filters={'imdb_id': parsed_id}))

    async def get_movies_by_fuzzy_title_match(
        self, query: str, similarity_threshold: float, limit: int
    ) -> list[MovieSchema]:
        movies = await self.movie_repo.get_by_similarity('title', query, similarity_threshold, limit)
        if not movies:
            return []
        return [MovieSchema.model_validate(movie) for movie in movies]

    async def get_movies_by_title_prefix_match(self, query: str, limit: int) -> list[MovieSchema]:
        movies = await self.movie_repo.get_by_prefix('title', query, limit)
        if not movies:
            return []
        return [MovieSchema.model_validate(movie) for movie in movies]

    async def get_movie_by_exact_title_search(self, query: str) -> list[Movie]:
        """Get movies by exact title search (case-insensitive)."""
        # The router expects list[Movie] (which it then validates), or list[MovieSchema]
        # Looking at router:
        # exact_match_result = await movie_service.get_movie_by_exact_title_search(query)
        # exact_match = [MovieSchema.model_validate(movie) for movie in exact_match_result]
        # So it expects Sequence[Movie]
        movies = await self.movie_repo.get_by_exact_ilike('title', query)
        return list(movies)

    async def get_movies_with_emotions_by_movielens_ids(self, movielens_ids: list[str]) -> list[MovieSchema]:
        # movies = await self.movie_repo.get_all_by_field_in_values(
        #     'movielens_id', movielens_ids, options=MovieRepository.LOAD_EMOTIONS
        # )

        movies = await self.movie_repo.find_many(
            RepoQueryOptions(filters={'movielens_id': movielens_ids}, load_options=MovieRepository.LOAD_EMOTIONS)
        )
        if not movies:
            return []
        return [MovieSchema.model_validate(movie) for movie in movies]

    @alru_cache(maxsize=128)
    async def get_movies(self, limit: int, offset: int, ordering: str = 'none') -> list[MovieSchema]:
        repo_options = RepoQueryOptions(limit=limit, offset=offset)
        if ordering and ordering != 'none':
            repo_options.sort_by = ordering

        movies = await self.movie_repo.find_many(repo_options)
        if not movies:
            return []
        return [MovieSchema.model_validate(movie) for movie in movies]

    @alru_cache(maxsize=128)
    async def get_movies_with_details(self, limit: int, offset: int) -> list[MovieDetailSchema]:
        # movies = await self.movie_repo.get_paged(limit, offset, options=MovieRepository.LOAD_FULL_DETAILS)

        movies = await self.movie_repo.find_many(
            RepoQueryOptions(limit=limit, offset=offset, load_options=MovieRepository.LOAD_ALL)
        )
        if not movies:
            return []
        return [MovieDetailSchema.model_validate(movie) for movie in movies]

    @alru_cache(maxsize=1)
    async def get_movie_count(self) -> int:
        return await self.movie_repo.count()
