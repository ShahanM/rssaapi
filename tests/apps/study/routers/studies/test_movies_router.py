"""Tests for the movies router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.movies import router
from rssa_api.auth.authorization import get_current_participant, validate_study_participant
from rssa_api.data.schemas.participant_schemas import StudyParticipantRead
from rssa_api.data.services.dependencies import MovieServiceDep, StudyParticipantMovieSessionServiceDep
from rssa_api.data.services.movie_service import MovieService
from rssa_api.data.services.study_participants import StudyParticipantMovieSessionService


def get_dependency_key(annotated_dep: Any) -> Any:
    """Extracts the dependency function from an Annotated dependency."""
    for item in get_args(annotated_dep):
        if isinstance(item, FastAPI_Depends):
            return item.dependency
    raise ValueError(f'Could not find Depends in {annotated_dep}')


@pytest.fixture
def mock_movie_service() -> AsyncMock:
    """Fixture for mocked MovieService."""
    return AsyncMock(spec=MovieService)


@pytest.fixture
def mock_session_service() -> AsyncMock:
    """Fixture for mocked StudyParticipantMovieSessionService."""
    return AsyncMock(spec=StudyParticipantMovieSessionService)


@pytest.fixture
def client(
    mock_movie_service: AsyncMock,
    mock_session_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_dependency_key(MovieServiceDep)] = lambda: mock_movie_service
    app.dependency_overrides[get_dependency_key(StudyParticipantMovieSessionServiceDep)] = lambda: mock_session_service

    # Mock Auth
    # /movies/ers uses get_current_participant -> StudyParticipantRead
    async def mock_get_participant() -> MagicMock:
        participant = MagicMock(spec=StudyParticipantRead)
        participant.id = uuid.uuid4()
        participant.study_id = uuid.uuid4()
        return participant

    app.dependency_overrides[get_current_participant] = mock_get_participant

    # /movies/ uses validate_study_participant -> dict
    async def mock_validate_participant() -> dict[str, uuid.UUID]:
        return {'pid': uuid.uuid4(), 'sid': uuid.uuid4()}

    app.dependency_overrides[validate_study_participant] = mock_validate_participant

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_movies_with_emotions_success(
    client: TestClient, mock_movie_service: AsyncMock, mock_session_service: AsyncMock
) -> None:
    """Test retrieving movies with emotions."""
    # Mock session return
    movie_id = uuid.uuid4()
    mock_session_result = MagicMock()
    mock_session_result.movies = [movie_id]
    mock_session_service.get_next_session_movie_ids_batch.return_value = mock_session_result

    # Mock movies
    mock_movie1 = MagicMock()
    mock_movie1.id = movie_id
    mock_movie1.title = 'Movie 1'
    mock_movie1.year = 2023
    mock_movie1.genres = ['Action']
    mock_movie1.tmdb_id = '101'
    mock_movie1.poster_path = '/path1'
    mock_movie1.poster_full_path = 'http://path1'
    mock_movie1.imdb_id = 'tt1'
    mock_movie1.movielens_id = 'ml1'
    mock_movie1.genre = 'Action'
    mock_movie1.director = 'Director'
    mock_movie1.cast = 'Cast'
    mock_movie1.description = 'Desc'
    mock_movie1.poster = 'poster.jpg'
    mock_movie1.tmdb_poster = 'tmdb.jpg'
    mock_movie1.poster_identifier = 'pid'
    mock_movie1.ave_rating = 5.0
    mock_movie1.imdb_avg_rating = 8.0
    mock_movie1.imdb_rate_count = 100
    mock_movie1.tmdb_avg_rating = 8.0
    mock_movie1.tmdb_rate_count = 100

    mock_movie_service.get_movies_with_emotions_from_ids.return_value = [mock_movie1]

    response = client.get('/movies/ers')

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == 'Movie 1'


@pytest.mark.asyncio
async def test_get_movies_success(
    client: TestClient, mock_movie_service: AsyncMock, mock_session_service: AsyncMock
) -> None:
    """Test retrieving paginated movies."""
    # Mock session return
    movie_id = uuid.uuid4()
    mock_session_result = MagicMock()
    mock_session_result.movies = [movie_id]
    mock_session_result.total = 10
    mock_session_service.get_next_session_movie_ids_batch.return_value = mock_session_result

    # Mock movies
    mock_movie = MagicMock()
    mock_movie.id = movie_id
    mock_movie.title = 'Movie 1'
    mock_movie.year = 2023
    mock_movie.genres = ['Action']
    mock_movie.tmdb_id = '101'
    mock_movie.poster_path = '/path1'
    mock_movie.poster_full_path = 'http://path1'
    mock_movie.imdb_id = 'tt1'
    mock_movie.movielens_id = 'ml1'
    mock_movie.genre = 'Action'
    mock_movie.director = 'Director'
    mock_movie.cast = 'Cast'
    mock_movie.description = 'Desc'
    mock_movie.poster = 'poster.jpg'
    mock_movie.tmdb_poster = 'tmdb.jpg'
    mock_movie.poster_identifier = 'pid'
    mock_movie.ave_rating = 5.0
    mock_movie.imdb_avg_rating = 8.0
    mock_movie.imdb_rate_count = 100
    mock_movie.tmdb_avg_rating = 8.0
    mock_movie.tmdb_rate_count = 100
    mock_movie.emotions = None
    mock_movie.recommendations_text = None

    mock_movie_service.get_movies_from_ids.return_value = [mock_movie]

    response = client.get('/movies/')

    assert response.status_code == 200, response.text
    data = response.json()
    assert data['count'] == 10
    assert len(data['data']) == 1


@pytest.mark.asyncio
async def test_search_movie_exact_match(client: TestClient, mock_movie_service: AsyncMock) -> None:
    """Test searching movies with exact match."""
    payload = {'query': 'Inception'}
    movie_id = uuid.uuid4()

    mock_movie = MagicMock()
    mock_movie.id = movie_id
    mock_movie.title = 'Inception'
    mock_movie.year = 2010
    mock_movie.genres = ['Sci-Fi']
    mock_movie.tmdb_id = '101'
    mock_movie.poster_path = '/path1'
    mock_movie.poster_full_path = 'http://path1'
    mock_movie.imdb_id = 'tt1'
    mock_movie.movielens_id = 'ml1'
    mock_movie.genre = 'Sci-Fi'
    mock_movie.director = 'Nolan'
    mock_movie.cast = 'Leo'
    mock_movie.description = 'Dreams'
    mock_movie.poster = 'poster.jpg'
    mock_movie.tmdb_poster = 'tmdb.jpg'
    mock_movie.poster_identifier = 'pid'
    mock_movie.ave_rating = 9.0
    mock_movie.imdb_avg_rating = 9.0
    mock_movie.imdb_rate_count = 1000
    mock_movie.tmdb_avg_rating = 9.0
    mock_movie.tmdb_rate_count = 1000

    mock_movie_service.get_movie_by_exact_title_search.return_value = [mock_movie]

    response = client.post('/movies/search', json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == 'Inception'


@pytest.mark.asyncio
async def test_search_movie_fuzzy_match(client: TestClient, mock_movie_service: AsyncMock) -> None:
    """Test searching movies with fuzzy match when exact match fails."""
    payload = {'query': 'Incept'}
    movie_id = uuid.uuid4()

    mock_movie_service.get_movie_by_exact_title_search.return_value = []

    mock_movie = MagicMock()
    mock_movie.id = movie_id
    mock_movie.title = 'Inception'
    mock_movie.year = 2010
    mock_movie.genres = ['Sci-Fi']
    mock_movie.tmdb_id = '101'
    mock_movie.poster_path = '/path1'
    mock_movie.poster_full_path = 'http://path1'
    mock_movie.imdb_id = 'tt1'
    mock_movie.movielens_id = 'ml1'
    mock_movie.genre = 'Sci-Fi'
    mock_movie.director = 'Nolan'
    mock_movie.cast = 'Leo'
    mock_movie.description = 'Dreams'
    mock_movie.poster = 'poster.jpg'
    mock_movie.tmdb_poster = 'tmdb.jpg'
    mock_movie.poster_identifier = 'pid'
    mock_movie.ave_rating = 9.0
    mock_movie.imdb_avg_rating = 9.0
    mock_movie.imdb_rate_count = 1000
    mock_movie.tmdb_avg_rating = 9.0
    mock_movie.tmdb_rate_count = 1000

    mock_movie_service.get_movies_by_fuzzy_title_match.return_value = [mock_movie]
    mock_movie_service.get_movies_by_title_prefix_match.return_value = []

    response = client.post('/movies/search', json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == 'Inception'
