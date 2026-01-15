"""Tests for MovieService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rssa_storage.moviedb.models.movies import Movie
from rssa_storage.moviedb.repositories import MovieRepository

from rssa_api.data.services.movie_service import MovieService


@pytest.fixture
def mock_repo() -> AsyncMock:
    """Fixture for a mocked MovieRepository."""
    return AsyncMock(spec=MovieRepository)


@pytest.fixture
def service(mock_repo: AsyncMock) -> MovieService:
    """Fixture for the MovieService."""
    return MovieService(mock_repo)


def create_mock_movie(mid: int) -> MagicMock:
    """Helper to create a mock movie object."""
    m = MagicMock(spec=Movie)
    m.id = uuid.uuid4()
    m.movielens_id = str(mid)
    m.title = f'Movie {mid}'
    m.year = 2021
    m.emotions = MagicMock()  # Needs to satisfy schema validation if we use schema
    # Helper to make it valid for schema
    return m


# We patch schema validation in MovieService to avoid complex mock setup for SQLModels
@pytest.fixture
def mock_schemas(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock Schema validation to simplify tests."""
    # Mock model_validate to just return a dict or simple object
    mock_schema = MagicMock()
    mock_schema.model_validate.side_effect = lambda x: x  # pass through
    return mock_schema


@pytest.mark.asyncio
async def test_get_movies_with_emotions(service: MovieService, mock_repo: AsyncMock) -> None:
    """Test retrieving movies with emotions loaded."""
    mock_repo.find_many.return_value = ['movie1', 'movie2']

    result = await service.get_movies_with_emotions()

    assert len(result) == 2
    mock_repo.find_many.assert_called_once()
    opts = mock_repo.find_many.call_args[0][0]
    assert opts.load_options is not None


@pytest.mark.asyncio
async def test_get_movies_from_ids(service: MovieService, mock_repo: AsyncMock) -> None:
    """Test retrieving movies by a list of UUIDs."""
    ids = [uuid.uuid4()]
    movie = create_mock_movie(1)
    mock_repo.find_many.return_value = [movie]

    # We need real validation or mock it.
    # Let's try to make the movie mock compatible enough or patch MovieDetailSchema
    with patch('rssa_api.data.services.movie_service.MovieDetailSchema') as MockSchema:
        MockSchema.model_validate.return_value = 'ValidatedMovie'

        result = await service.get_movies_from_ids(ids)

        assert result == ['ValidatedMovie']
        MockSchema.model_validate.assert_called_with(movie)


@pytest.mark.asyncio
async def test_get_movie_by_movielens_id(service: MovieService, mock_repo: AsyncMock) -> None:
    """Test retrieving a movie by its MovieLens ID."""
    mock_repo.find_one.return_value = 'movie'
    res = await service.get_movie_by_movielens_id('101')
    assert res == 'movie'
    opts = mock_repo.find_one.call_args[0][0]
    assert opts.filters == {'movielens_id': '101'}


@pytest.mark.asyncio
async def test_get_movies_by_fuzzy_title(service: MovieService, mock_repo: AsyncMock) -> None:
    """Test searching for movies by fuzzy title matching."""
    mock_repo.get_by_similarity.return_value = ['m1']

    with patch('rssa_api.data.services.movie_service.MovieSchema') as MockSchema:
        MockSchema.model_validate.return_value = 'SchemaM1'
        res = await service.get_movies_by_fuzzy_title_match('query', 0.5, 10)
        assert res == ['SchemaM1']
        mock_repo.get_by_similarity.assert_called_with('title', 'query', 0.5, 10)


@pytest.mark.asyncio
async def test_get_movies_cached(service: MovieService, mock_repo: AsyncMock) -> None:
    """Test get_movies and verify caching logic (using alru_cache)."""
    # Note: alru_cache is on the method.
    mock_repo.find_many.return_value = []

    await service.get_movies(10, 0)
    await service.get_movies(10, 0)

    # Should call repo only once
    assert mock_repo.find_many.call_count == 1

    # Different args
    await service.get_movies(20, 0)
    assert mock_repo.find_many.call_count == 2
