"""Tests for the movies router."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.movies import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import MovieServiceDep
from rssa_api.data.services.movie_service import MovieService


@pytest.fixture
def mock_movie_service() -> AsyncMock:
    """Fixture for a mocked MovieService."""
    return AsyncMock(spec=MovieService)


@pytest.fixture
def client(mock_movie_service: AsyncMock) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    # Extract the actual dependency callable from Annotated
    from typing import get_args

    from fastapi.params import Depends as FastAPI_Depends

    dep_callable = None
    for item in get_args(MovieServiceDep):
        if isinstance(item, FastAPI_Depends):
            dep_callable = item.dependency
            break

    if dep_callable:
        app.dependency_overrides[dep_callable] = lambda: mock_movie_service
    else:
        # Fallback if extraction fails (shouldn't happen with correct typing)
        app.dependency_overrides[MovieServiceDep] = lambda: mock_movie_service

    # Mock Auth0 user
    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(sub='auth0|user123', email='user@test.com', permissions=['admin:all', 'read:movies'])

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_movies_summary_success(client: TestClient, mock_movie_service: AsyncMock) -> None:
    """Test retrieving movie summaries."""
    # Using simple dicts for mocks as they are easy to model_validate
    mock_movies = [
        {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'title': 'Test Movie',
            'year': 2000,
            'genre': 'Action',
            'description': 'Desc',
            'poster': 'poster.jpg',
        }
    ]

    # The service returns SQLModel objects usually, but Pydantic model_validate handles dicts too.
    # To be safer let's make them look like objects.
    class MockMovie:
        id = '123e4567-e89b-12d3-a456-426614174000'
        title = 'Test Movie'
        year = 2000
        genre = 'Action'
        description = 'Desc'
        poster = 'poster.jpg'
        ave_rating = 4.5
        imdb_avg_rating = 7.8
        imdb_rate_count = 1000
        tmdb_avg_rating = 7.5
        tmdb_rate_count = 500
        director = 'Director'
        cast = 'Cast'
        imdb_id = 'tt123'
        tmdb_id = '123'
        movielens_id = '1'
        poster_identifier = ''
        tmdb_poster = ''

    mock_movie_service.get_movies.return_value = [MockMovie()]

    response = client.get('/movies/summary?offset=0&limit=10')

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == 'Test Movie'
    mock_movie_service.get_movies.assert_called_once_with(
        10, 0, title=None, year_min=None, year_max=None, genre=None, sort_by=None
    )


@pytest.mark.asyncio
async def test_get_movies_with_details_success(client: TestClient, mock_movie_service: AsyncMock) -> None:
    """Test retrieving movies with full details."""

    class MockMovieDetail:
        id = '123e4567-e89b-12d3-a456-426614174000'
        title = 'Test Movie'
        year = 2000
        genre = 'Action'
        description = 'Desc'
        poster = 'poster.jpg'
        ave_rating = 4.5
        imdb_avg_rating = 7.8
        imdb_rate_count = 1000
        tmdb_avg_rating = 7.5
        tmdb_rate_count = 500
        director = 'Director'
        cast = 'Cast'
        imdb_id = 'tt123'
        tmdb_id = '123'
        movielens_id = '1'
        poster_identifier = ''
        tmdb_poster = ''

        # Detail fields
        emotions = None
        recommendations_text = None

    mock_movie_service.get_movies_with_details.return_value = [MockMovieDetail()]
    mock_movie_service.get_movie_count.return_value = 1

    response = client.get('/movies/?offset=0&limit=10')

    assert response.status_code == 200, response.text
    data = response.json()
    assert data['count'] == 1
    assert len(data['data']) == 1
    assert data['data'][0]['title'] == 'Test Movie'
    mock_movie_service.get_movies_with_details.assert_called_once_with(
        10, 0, title=None, year_min=None, year_max=None, genre=None, sort_by=None
    )
    mock_movie_service.get_movie_count.assert_called_once_with(
        title=None, year_min=None, year_max=None, genre=None
    )


@pytest.mark.asyncio
async def test_create_movie_reviews(client: TestClient, mock_movie_service: AsyncMock) -> None:
    """Test adding reviews to a movie."""
    payload = {
        'imdb_id': 'tt1234567',
        'reviews': [{'text': 'Great movie content', 'helpful': 10, 'unhelpful': 2, 'date': '2023-01-01'}],
    }

    mock_movie_service.get_movie_by_imdb_id.return_value = MagicMock()

    response = client.post('/movies/reviews', json=payload)

    assert response.status_code == 201
    assert response.json()['message'] == 'Reviews added to the movie.'
    mock_movie_service.get_movie_by_imdb_id.assert_called_once_with('tt1234567')
    mock_movie_service.get_movie_by_imdb_id.assert_called_once_with('tt1234567')


@pytest.mark.asyncio
async def test_update_movie_success(client: TestClient, mock_movie_service: AsyncMock) -> None:
    """Test updating movie details."""
    movie_id = '123e4567-e89b-12d3-a456-426614174000'
    payload = {'title': 'Updated Title', 'year': 2023}
    
    # Mock return value should look like a movie schema
    class MockMovie:
        id = movie_id
        title = 'Updated Title'
        year = 2023
        genre = 'Action'
        description = 'Desc'
        poster = 'poster.jpg'
        ave_rating = 4.5
        imdb_avg_rating = 7.8
        imdb_rate_count = 1000
        tmdb_avg_rating = 7.5
        tmdb_rate_count = 500
        director = 'Director'
        cast = 'Cast'
        imdb_id = 'tt123'
        tmdb_id = '123'
        movielens_id = '1'
        poster_identifier = ''
        tmdb_poster = ''

    mock_movie_service.update_movie.return_value = MockMovie()

    response = client.patch(f'/movies/{movie_id}', json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'Updated Title'
    assert data['year'] == 2023
    
    # Verify the service was called with correct UUID and schema
    mock_movie_service.update_movie.assert_called_once()
    args = mock_movie_service.update_movie.call_args
    assert str(args[0][0]) == movie_id
    assert args[0][1].title == 'Updated Title'
    assert args[0][1].year == 2023

@pytest.mark.asyncio
async def test_update_movie_ratings_success(client: TestClient, mock_movie_service: AsyncMock) -> None:
    """Test updating movie ratings successfully when both rating and count are provided."""
    movie_id = '123e4567-e89b-12d3-a456-426614174000'
    payload = {'imdb_avg_rating': 8.5, 'imdb_rate_count': 100}

    class MockMovie:
        id = movie_id
        title = 'Movie Title'
        year = 2023
        genre = 'Action'
        description = 'Desc'
        poster = 'poster.jpg'
        ave_rating = 8.5
        imdb_avg_rating = 8.5
        imdb_rate_count = 100
        tmdb_avg_rating = 7.5
        tmdb_rate_count = 500
        director = 'Director'
        cast = 'Cast'
        imdb_id = 'tt123'
        tmdb_id = '123'
        movielens_id = '1'
        poster_identifier = ''
        tmdb_poster = ''

    mock_movie_service.update_movie.return_value = MockMovie()

    response = client.patch(f'/movies/{movie_id}', json=payload)
    assert response.status_code == 200
    mock_movie_service.update_movie.assert_called_once()


@pytest.mark.asyncio
async def test_update_movie_ratings_fail_missing_count(client: TestClient, mock_movie_service: AsyncMock) -> None:
    """Test that updating rating without count fails."""
    movie_id = '123e4567-e89b-12d3-a456-426614174000'
    payload = {'imdb_avg_rating': 8.5}

    response = client.patch(f'/movies/{movie_id}', json=payload)
    assert response.status_code == 422
    assert 'must be provided together' in response.text
