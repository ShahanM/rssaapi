"""Movie service for handling movie related operations."""

import uuid
from typing import Any

from async_lru import alru_cache
from rssa_storage.moviedb.models.movies import Movie
from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.shared import RepoQueryOptions, merge_repo_query_options

from rssa_api.data.schemas.movie_schemas import MovieDetailSchema, MovieSchema, MovieUpdateSchema
from rssa_api.data.services.base_service import BaseService


class MovieService(BaseService[Movie, MovieRepository]):
    """Movie service for handling movie related operations."""

    def __init__(self, movie_repo: MovieRepository):
        """Initialize the movie service."""
        self.movie_repo = movie_repo

    async def get_movies_with_emotions(self) -> list[Movie]:
        """Get all movies with emotions."""
        # return await self.movie_repo.get_all(options=MovieRepository.LOAD_EMOTIONS)
        movies = await self.movie_repo.find_many(RepoQueryOptions(load_options=MovieRepository.LOAD_ALL))
        return list(movies)

    async def get_movies_from_ids(self, movie_ids: list[uuid.UUID]) -> list[MovieDetailSchema]:
        """Get movies from ids.

        Args:
            movie_ids: List of movie ids.

        Returns:
            List of movie details.
        """
        movies = await self.movie_repo.find_many(RepoQueryOptions(ids=movie_ids, load_options=MovieRepository.LOAD_ALL))
        if not movies:
            return []
        return [MovieDetailSchema.model_validate(movie) for movie in movies]

    async def get_movies_with_emotions_from_ids(self, movie_ids: list[uuid.UUID]) -> list[Movie]:
        """Get movies with emotions from ids.

        Args:
            movie_ids: List of movie ids.

        Returns:
            List of movies with emotions.
        """
        movies = await self.movie_repo.find_many(
            RepoQueryOptions(ids=movie_ids, load_options=MovieRepository.LOAD_EMOTIONS)
        )
        if not movies:
            return []
        return list(movies)

    async def get_movies_by_movielens_ids(self, movielens_ids: list[str | int]) -> list[Movie]:
        """Get movies by movielens ids.

        Args:
            movielens_ids: List of movielens ids.

        Returns:
            List of movies.
        """
        movies = await self.movie_repo.find_many(RepoQueryOptions(filters={'movielens_id': movielens_ids}))
        return list(movies)

    async def get_movie_by_movielens_id(self, movielens_id: str) -> Movie | None:
        """Get movie by movielens id.

        Args:
            movielens_id: The movielens id of the movie.

        Returns:
            Movie | None: The movie with the given movielens id.
        """
        return await self.movie_repo.find_one(RepoQueryOptions(filters={'movielens_id': movielens_id}))

    async def get_movie_details_by_movielens_id(self, movielens_id: str) -> MovieDetailSchema:
        """Get movie details by movielens id.

        Args:
            movielens_id: The movielens id of the movie.

        Returns:
            MovieDetailSchema: The movie details with the given movielens id.
        """
        movie = await self.movie_repo.find_one(
            RepoQueryOptions(filters={'movielens_id': movielens_id}, load_options=MovieRepository.LOAD_ALL)
        )
        return MovieDetailSchema.model_validate(movie)

    async def get_movie_by_imdb_id(self, imdb_id: str) -> Movie | None:
        """Get movie by imdb id.

        Args:
            imdb_id: The imdb id of the movie.

        Returns:
            Movie | None: The movie with the given imdb id.
        """
        parsed_id = imdb_id[2:] if imdb_id[:2].lower() == 'tt' else imdb_id

        return await self.movie_repo.find_one(RepoQueryOptions(filters={'imdb_id': parsed_id}))

    async def get_movies_by_fuzzy_title_match(
        self, query: str, similarity_threshold: float, limit: int
    ) -> list[MovieSchema]:
        """Get movies by fuzzy title match.

        Args:
            query: The query to search for.
            similarity_threshold: The similarity threshold.
            limit: The limit of movies to return.

        Returns:
            list[MovieSchema]: The movies that match the given query.
        """
        movies = await self.movie_repo.get_by_similarity('title', query, similarity_threshold, limit)
        if not movies:
            return []
        return [MovieSchema.model_validate(movie) for movie in movies]

    async def get_movies_by_title_prefix_match(self, query: str, limit: int) -> list[MovieSchema]:
        """Get movies by title prefix match.

        Args:
            query: The query to search for.
            limit: The limit of movies to return.

        Returns:
            list[MovieSchema]: The movies that match the given query.
        """
        movies = await self.movie_repo.get_by_prefix('title', query, limit)
        if not movies:
            return []
        return [MovieSchema.model_validate(movie) for movie in movies]

    async def get_movie_by_exact_title_search(self, query: str) -> list[Movie]:
        """Get movies by exact title search (case-insensitive).

        Args:
            query: The query to search for.

        Returns:
            list[Movie]: The movies that match the given query.
        """
        movies = await self.movie_repo.get_by_exact_ilike('title', query)
        return list(movies)

    async def get_movies_with_emotions_by_movielens_ids(self, movielens_ids: list[str]) -> list[MovieSchema]:
        """Get movies with emotions that match the given movielens ids.

        Args:
            movielens_ids: The movielens ids to match.

        Returns:
            list[MovieSchema]: The movies with emotions that match the given movielens ids.
        """
        movies = await self.movie_repo.find_many(
            RepoQueryOptions(filters={'movielens_id': movielens_ids}, load_options=MovieRepository.LOAD_EMOTIONS)
        )
        if not movies:
            return []
        return [MovieSchema.model_validate(movie) for movie in movies]

    def _build_repo_query_options(
        self,
        limit: int,
        offset: int,
        title: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        genre: str | None = None,
        ordering: str | None = 'none',
        sort_by: str | None = None,
        sort_desc: bool = False,
        exclude_no_emotions: bool = False,
        exclude_no_recommendations: bool = False,
        load_options: list[Any] | None = None,
    ) -> RepoQueryOptions:
        """Build repository query options from filters.

        Args:
            limit: The number of movies to return.
            offset: The offset to start from.
            title: The title of the movie to search for.
            year_min: The minimum year of the movie to search for.
            year_max: The maximum year of the movie to search for.
            genre: The genre of the movie to search for.
            ordering: The ordering to use.
            sort_by: The field to sort by.
            sort_desc: Whether to sort in descending order.
            exclude_no_emotions: Whether to exclude movies with no emotions.
            exclude_no_recommendations: Whether to exclude movies with no recommendations.
            load_options: Loading options for the query.

        Returns:
            RepoQueryOptions: The constructed query options.
        """
        repo_options = RepoQueryOptions(limit=limit, offset=offset)

        if load_options:
            repo_options.load_options = load_options

        sort_options = self._build_ordering_query_options(sort_by, sort_desc, ordering)
        repo_options = merge_repo_query_options(repo_options, sort_options)

        filter_options = self._build_filter_query_options(year_min, year_max, genre, title)
        repo_options = merge_repo_query_options(repo_options, filter_options)

        exclude_options = self._build_exclude_query_options(exclude_no_emotions, exclude_no_recommendations)
        repo_options = merge_repo_query_options(repo_options, exclude_options)

        return repo_options

    def _build_ordering_query_options(
        self,
        sort_by: str | None = None,
        sort_desc: bool = False,
        ordering: str | None = 'none',
    ) -> RepoQueryOptions:
        """Build ordering query options from filters.

        Args:
            sort_by: The field to sort by.
            sort_desc: Whether to sort in descending order.
            ordering: The ordering to use.

        Returns:
            RepoQueryOptions: The constructed query options.
        """
        repo_options = RepoQueryOptions()
        if sort_by:
            if sort_by.startswith('-'):
                repo_options.sort_by = sort_by[1:]
                repo_options.sort_desc = True
            else:
                repo_options.sort_by = sort_by
        elif ordering and ordering != 'none':
            repo_options.sort_by = ordering
        return repo_options

    def _build_filter_query_options(
        self,
        year_min: int | None = None,
        year_max: int | None = None,
        genre: str | None = None,
        title: str | None = None,
    ) -> RepoQueryOptions:
        """Build filter query options from filters.

        Args:
            year_min: The minimum year of the movie to search for.
            year_max: The maximum year of the movie to search for.
            genre: The genre of the movie to search for.
            title: The title of the movie to search for.

        Returns:
            RepoQueryOptions: The constructed query options.
        """
        repo_options = RepoQueryOptions()
        if year_min is not None:
            repo_options.filter_ranges.append(('year', '>=', year_min))
        if year_max is not None:
            repo_options.filter_ranges.append(('year', '<=', year_max))
        if genre:
            repo_options.filter_ilike['genre'] = genre
        if title:
            repo_options.filter_ilike['title'] = title
        return repo_options

    def _build_exclude_query_options(
        self, exclude_no_emotions: bool = False, exclude_no_recommendations: bool = False
    ) -> RepoQueryOptions:
        """Build exclude query options from filters.

        Args:
            exclude_no_emotions: Whether to exclude movies with no emotions.
            exclude_no_recommendations: Whether to exclude movies with no recommendations.

        Returns:
            RepoQueryOptions: The constructed query options.
        """
        repo_options = RepoQueryOptions()
        if exclude_no_emotions:
            repo_options.filter_not_null.append('emotions')
        if exclude_no_recommendations:
            repo_options.filter_not_null.append('recommendations_text')
        return repo_options

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
        exclude_no_emotions: bool = False,
        exclude_no_recommendations: bool = False,
    ) -> list[MovieSchema]:
        """Get movies that match the given filters.

        Args:
            limit: The number of movies to return.
            offset: The offset to start from.
            title: The title of the movie to search for.
            year_min: The minimum year of the movie to search for.
            year_max: The maximum year of the movie to search for.
            genre: The genre of the movie to search for.
            ordering: The ordering to use.
            sort_by: The field to sort by.
            exclude_no_emotions: Whether to exclude movies with no emotions.
            exclude_no_recommendations: Whether to exclude movies with no recommendations.

        Returns:
            list[MovieSchema]: The movies that match the given filters.
        """
        repo_options = self._build_repo_query_options(
            limit=limit,
            offset=offset,
            title=title,
            year_min=year_min,
            year_max=year_max,
            genre=genre,
            ordering=ordering,
            sort_by=sort_by,
            exclude_no_emotions=exclude_no_emotions,
            exclude_no_recommendations=exclude_no_recommendations,
        )

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
        exclude_no_emotions: bool = False,
        exclude_no_recommendations: bool = False,
    ) -> list[MovieDetailSchema]:
        """Get movies with details that match the given filters.

        Args:
            limit: The number of movies to return.
            offset: The offset to start from.
            title: The title of the movie to search for.
            year_min: The minimum year of the movie to search for.
            year_max: The maximum year of the movie to search for.
            genre: The genre of the movie to search for.
            sort_by: The field to sort by.
            exclude_no_emotions: Whether to exclude movies with no emotions.
            exclude_no_recommendations: Whether to exclude movies with no recommendations.

        Returns:
            list[MovieDetailSchema]: The movies that match the given filters.
        """
        repo_options = self._build_repo_query_options(
            limit=limit,
            offset=offset,
            title=title,
            year_min=year_min,
            year_max=year_max,
            genre=genre,
            sort_by=sort_by,
            exclude_no_emotions=exclude_no_emotions,
            exclude_no_recommendations=exclude_no_recommendations,
            load_options=[MovieRepository.LOAD_ALL],
        )

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
        exclude_no_emotions: bool = False,
        exclude_no_recommendations: bool = False,
    ) -> int:
        """Get the count of movies that match the given filters.

        Args:
            title: The title of the movie to search for.
            year_min: The minimum year of the movie to search for.
            year_max: The maximum year of the movie to search for.
            genre: The genre of the movie to search for.
            exclude_no_emotions: Whether to exclude movies with no emotions.
            exclude_no_recommendations: Whether to exclude movies with no recommendations.

        Returns:
            int: The count of movies that match the given filters.
        """
        filter_ranges = []
        filter_ilike = {}
        filter_not_null = []

        if year_min is not None:
            filter_ranges.append(('year', '>=', year_min))
        if year_max is not None:
            filter_ranges.append(('year', '<=', year_max))
        if genre:
            filter_ilike['genre'] = genre
        if title:
            filter_ilike['title'] = title

        if exclude_no_emotions:
            filter_not_null.append('emotions')
        if exclude_no_recommendations:
            filter_not_null.append('recommendations_text')

        return await self.movie_repo.count(
            filter_ranges=filter_ranges, filter_ilike=filter_ilike, filter_not_null=filter_not_null
        )

    async def update_movie(self, movie_id: uuid.UUID, update_data: MovieUpdateSchema) -> Movie | None:
        """Update a movie with the provided data.

        Args:
            movie_id: The ID of the movie to update.
            update_data: The data to update the movie with.

        Returns:
            Movie | None: The updated movie, or None if the movie does not exist.
        """
        query_options = RepoQueryOptions(ids=[movie_id])
        existing_movie = await self.movie_repo.find_one(query_options)

        if not existing_movie:
            return None

        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

        if not update_dict:
            return existing_movie

        updated_movie = await self.movie_repo.update(movie_id, update_dict)
        return updated_movie
