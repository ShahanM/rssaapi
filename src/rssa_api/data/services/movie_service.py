import uuid

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

    async def get_movie_by_movielens_id(self, movielens_id: str) -> Movie | None:
        return await self.movie_repo.find_one(RepoQueryOptions(filters={'movielens_id': movielens_id}))

    async def get_movie_details_by_movielens_id(self, movielens_id: str) -> MovieDetailSchema:
        movie = await self.movie_repo.find_one(
            RepoQueryOptions(filters={'movielens_id': movielens_id}, load_options=MovieRepository.LOAD_ALL)
        )
        return MovieDetailSchema.model_validate(movie)

    async def get_movie_by_imdb_id(self, imdb_id: str) -> Movie | None:
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
    async def get_movies(
        self,
        limit: int,
        offset: int,
        title: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        genre: str | None = None,
        ordering: str | None = 'none',
        sort_by: str | None = None,
    ) -> list[MovieSchema]:
        repo_options = RepoQueryOptions(limit=limit, offset=offset)

        # Handle sorting
        if sort_by:
            if sort_by.startswith('-'):
                repo_options.sort_by = sort_by[1:]
                repo_options.sort_desc = True
            else:
                repo_options.sort_by = sort_by
        elif ordering and ordering != 'none':
            repo_options.sort_by = ordering

        # Handle filters
        if year_min is not None:
            repo_options.filter_ranges.append(('year', '>=', year_min))
        if year_max is not None:
            repo_options.filter_ranges.append(('year', '<=', year_max))
        if genre:
            repo_options.filter_ilike['genre'] = genre
        if title:
            # Using specific column search instead of broad search
            repo_options.filter_ilike['title'] = title

        movies = await self.movie_repo.find_many(repo_options)
        if not movies:
            return []
        return [MovieSchema.model_validate(movie) for movie in movies]

    @alru_cache(maxsize=128)
    async def get_movies_with_details(
        self,
        limit: int,
        offset: int,
        title: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        genre: str | None = None,
        sort_by: str | None = None,
    ) -> list[MovieDetailSchema]:
        # movies = await self.movie_repo.get_paged(limit, offset, options=MovieRepository.LOAD_FULL_DETAILS)

        repo_options = RepoQueryOptions(limit=limit, offset=offset, load_options=MovieRepository.LOAD_ALL)

        if sort_by:
            if sort_by.startswith('-'):
                repo_options.sort_by = sort_by[1:]
                repo_options.sort_desc = True
            else:
                repo_options.sort_by = sort_by

        if year_min is not None:
            repo_options.filter_ranges.append(('year', '>=', year_min))
        if year_max is not None:
            repo_options.filter_ranges.append(('year', '<=', year_max))
        if genre:
            repo_options.filter_ilike['genre'] = genre
        if title:
            repo_options.filter_ilike['title'] = title

        movies = await self.movie_repo.find_many(repo_options)
        if not movies:
            return []
        return [MovieDetailSchema.model_validate(movie) for movie in movies]

    @alru_cache(maxsize=1)
    async def get_movie_count(
        self,
        title: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        genre: str | None = None,
    ) -> int:
        filter_ranges = []
        filter_ilike = {}

        if year_min is not None:
            filter_ranges.append(('year', '>=', year_min))
        if year_max is not None:
            filter_ranges.append(('year', '<=', year_max))
        if genre:
            filter_ilike['genre'] = genre
        if title:
            filter_ilike['title'] = title

        return await self.movie_repo.count(filter_ranges=filter_ranges, filter_ilike=filter_ilike)

    async def update_movie(self, movie_id: uuid.UUID, update_data: 'MovieUpdateSchema') -> Movie | None:
        """Update a movie with the provided data."""
        # Check if movie exists
        query_options = RepoQueryOptions(ids=[movie_id])
        existing_movie = await self.movie_repo.find_one(query_options)
        
        if not existing_movie:
            return None

        # Filter out None values to only update provided fields
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            return existing_movie

        updated_movie = await self.movie_repo.update(movie_id, update_dict)
        return updated_movie
