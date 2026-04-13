"""Movie service for handling movie related operations."""

import uuid
from typing import Annotated, TypeVar

from async_lru import alru_cache
from fastapi import Depends
from pydantic import BaseModel
from rssa_storage.moviedb.models.movies import Movie
from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.shared import RepoQueryOptions, merge_repo_query_options

from rssa_api.data.schemas.movie_schemas import MovieSchema
from rssa_api.data.services.base_service import BaseService
from rssa_api.data.sources.moviedb import get_repository, get_service
from rssa_api.data.utility import extract_load_strategies

SchemaType = TypeVar('SchemaType', bound=BaseModel)


class MovieService(BaseService[Movie, MovieRepository]):
    """Movie service for handling movie related operations."""

    def __init__(self, movie_repo: MovieRepository):
        """Initialize the movie service."""
        self.repo = movie_repo

    async def get_movies_from_ids(self, schema: type[SchemaType], movie_ids: list[uuid.UUID]) -> list[SchemaType]:
        if not movie_ids:
            return []

        top_cols, rel_map = extract_load_strategies(schema)
        movies = await self.repo.find_many(
            RepoQueryOptions(ids=movie_ids, load_columns=top_cols, load_relationships=rel_map)
        )
        if not movies:
            return []

        movie_dict = {movie.id: movie for movie in movies}
        ordered_movies = [movie_dict[m_id] for m_id in movie_ids if m_id in movie_dict]

        return [schema.model_validate(movie) for movie in ordered_movies]

    async def get_movies_by_movielens_ids(
        self, schema: type[SchemaType], movielens_ids: list[str | int]
    ) -> list[SchemaType]:
        """Get movies by movielens ids.

        Args:
            schema: The shape of the movie object to return
            movielens_ids: List of movielens ids.

        Returns:
            List of movies.
        """
        top_cols, rel_map = extract_load_strategies(schema)
        movies = await self.get_all(
            schema,
            options=RepoQueryOptions(
                filters={'movielens_id': movielens_ids}, load_columns=top_cols, load_relationships=rel_map
            ),
        )
        return movies

    async def get_movie_by_imdb_id(self, schema: type[SchemaType], imdb_id: str) -> Movie | None:
        """Get movie by imdb id.

            schema: The shape of the movie object to return
            imdb_id: The imdb id of the movie.

        Returns:
            Movie | None: The movie with the given imdb id.
        """
        top_cols, rel_map = extract_load_strategies(schema)
        parsed_id = imdb_id[2:] if imdb_id[:2].lower() == 'tt' else imdb_id
        return await self.repo.find_one(
            RepoQueryOptions(filters={'imdb_id': parsed_id}, load_columns=top_cols, load_relationships=rel_map)
        )

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
        movies = await self.repo.get_by_similarity('title', query, similarity_threshold, limit)
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
        movies = await self.repo.get_by_prefix('title', query, limit)
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
        movies = await self.repo.get_by_exact_ilike('title', query)
        return list(movies)

    def _get_ordering_opts(
        self,
        limit: int,
        offset: int,
        sort_by: str | None = None,
        ordering: str | None = 'none',
    ) -> RepoQueryOptions:
        """Build ordering query options from filters.

        Args:
            limit: The number of movies to return.
            offset: The offset to start from.
            sort_by: The field to sort by.
            sort_desc: Whether to sort in descending order.
            ordering: The ordering to use.

        Returns:
            RepoQueryOptions: The constructed query options.
        """
        repo_options = RepoQueryOptions(limit=limit, offset=offset)
        if sort_by:
            if sort_by.startswith('-'):
                repo_options.sort_by = sort_by[1:]
                repo_options.sort_desc = True
            else:
                repo_options.sort_by = sort_by
        elif ordering and ordering != 'none':
            repo_options.sort_by = ordering
        return repo_options

    @staticmethod
    def get_filter_opts(
        title: str | None = None,
        genre: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        exclude_no_emotions: bool = False,
        exclude_no_recommendations: bool = False,
    ) -> RepoQueryOptions:
        """Build filter query options from filters.

        Args:
            title: The title of the movie to search for.
            year_min: The minimum year of the movie to search for.
            year_max: The maximum year of the movie to search for.
            genre: The genre of the movie to search for.
            title: The title of the movie to search for.
            exclude_no_emotions: Whether to exclude movies with no emotions.
            exclude_no_recommendations: Whether to exclude movies with no recommendations.

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
        if exclude_no_emotions:
            repo_options.filter_not_null.append('emotions')
        if exclude_no_recommendations:
            repo_options.filter_not_null.append('recommendations_text')
        return repo_options

    @alru_cache(maxsize=128)
    async def get_all_cached(
        self,
        schema: type[SchemaType],
        *,
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
    ) -> list[SchemaType]:
        """Get movies that match the given filters.

        Args:
            schema: Return schema shape.
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
            list[SchemaType]: The movies that match the given filters.
        """
        filter_opts = self.get_filter_opts(
            title, genre, year_min, year_max, exclude_no_emotions, exclude_no_recommendations
        )
        order_opts = self._get_ordering_opts(limit, offset, sort_by, ordering)

        opts = merge_repo_query_options(order_opts, filter_opts)
        return await self.get_all(schema, options=opts)

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
        opts = self.get_filter_opts(title, genre, year_min, year_max, exclude_no_emotions, exclude_no_recommendations)
        return await self.repo.count(opts)


MovieServiceDep = Annotated[MovieService, Depends(get_service(MovieService, get_repository(MovieRepository)))]
