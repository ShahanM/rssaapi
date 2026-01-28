"""Tests for permissions enforcement in admin routers."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.study_components.studies import router as studies_router
from rssa_api.apps.admin.routers.movies import router as movies_router
from rssa_api.apps.admin.routers.survey_constructs.survey_constructs import router as constructs_router
from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.data.services.dependencies import (
    StudyServiceDep,
    StudyParticipantServiceDep,
    StudyConditionServiceDep,
    MovieServiceDep,
    SurveyConstructServiceDep,
    SurveyItemServiceDep,
)
from rssa_api.data.schemas.study_components import StudyAudit, ConditionCountSchema
from rssa_api.data.schemas.movie_schemas import MovieSchema


@pytest.fixture
def mock_study_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_study_participant_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_study_condition_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_movie_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_construct_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_item_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def app(
    mock_study_service,
    mock_study_participant_service,
    mock_study_condition_service,
    mock_movie_service,
    mock_construct_service,
    mock_item_service,
) -> FastAPI:
    app = FastAPI()
    app.include_router(studies_router)
    app.include_router(movies_router)
    app.include_router(constructs_router)

    from typing import get_args
    from fastapi.params import Depends as FastAPI_Depends

    def override_dep(dep_type, mock_instance):
        dep_callable = None
        for item in get_args(dep_type):
            if isinstance(item, FastAPI_Depends):
                dep_callable = item.dependency
                break
        if dep_callable:
            app.dependency_overrides[dep_callable] = lambda: mock_instance
        else:
            app.dependency_overrides[dep_type] = lambda: mock_instance

    override_dep(StudyServiceDep, mock_study_service)
    override_dep(StudyParticipantServiceDep, mock_study_participant_service)
    override_dep(StudyConditionServiceDep, mock_study_condition_service)
    override_dep(MovieServiceDep, mock_movie_service)
    override_dep(SurveyConstructServiceDep, mock_construct_service)
    override_dep(SurveyItemServiceDep, mock_item_service)

    return app


@pytest.mark.asyncio
async def test_get_study_detail_success_owner(
    app: FastAPI, mock_study_service: AsyncMock, mock_study_condition_service: AsyncMock
) -> None:
    """Test accessing study details as an owner."""
    user_id = uuid.uuid4()
    study_id = uuid.uuid4()

    # Mock Auth0 user
    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|123', email='test@test.com', permissions=['read:authorized_studies']
    )
    # Mock DB user
    app.dependency_overrides[get_current_user] = lambda: UserSchema(
        id=user_id, email='test@test.com', permissions=[], auth0_sub='auth0|123'
    )

    # Mock service
    mock_study_service.get_detailed.return_value = StudyAudit(
        id=study_id,
        name='Test Study',
        owner_id=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        description='Test Description',
        total_participants=0,
        participants_by_condition=[],
    )
    mock_study_service.check_study_access.return_value = True
    mock_study_condition_service.get_participant_count_by_condition.return_value = []

    with TestClient(app) as client:
        response = client.get(f'/studies/{study_id}')

    assert response.status_code == 200
    mock_study_service.check_study_access.assert_called_with(study_id, user_id)


@pytest.mark.asyncio
async def test_get_study_detail_forbidden_non_owner(app: FastAPI, mock_study_service: AsyncMock) -> None:
    """Test accessing study details as non-owner returns 404 (IDOR protection)."""
    user_id = uuid.uuid4()
    study_id = uuid.uuid4()

    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|123', email='test@test.com', permissions=['read:authorized_studies']
    )
    app.dependency_overrides[get_current_user] = lambda: UserSchema(
        id=user_id, email='test@test.com', permissions=[], auth0_sub='auth0|123'
    )

    # Mock service to return a study, but check_access returns False
    mock_study_service.get_detailed.return_value = StudyAudit(
        id=study_id,
        name='Test Study',
        owner_id=uuid.uuid4(),  # Different owner
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        description='Test Description',
        total_participants=0,
        participants_by_condition=[],
    )
    mock_study_service.check_study_access.return_value = False

    with TestClient(app) as client:
        response = client.get(f'/studies/{study_id}')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Study not found.'
    mock_study_service.check_study_access.assert_called_with(study_id, user_id)


@pytest.mark.asyncio
async def test_update_movie_success(app: FastAPI, mock_movie_service: AsyncMock) -> None:
    """Test updating movie with correct permissions."""
    movie_id = uuid.uuid4()

    # Needs read:movies (router) AND update:movies (endpoint)
    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|123', email='test@test.com', permissions=['update:movies', 'read:movies']
    )

    created_at = datetime.utcnow()
    updated_at = datetime.utcnow()

    valid_movie = MovieSchema(
        id=movie_id,
        created_at=created_at,
        updated_at=updated_at,
        imdb_id='tt1234567',
        tmdb_id='12345',
        movielens_id='1',
        title='Updated',
        year=2023,
        ave_rating=8.0,
        imdb_avg_rating=8.5,
        imdb_rate_count=1000,
        tmdb_avg_rating=7.5,
        tmdb_rate_count=500,
        genre='Action',
        director='Director Name',
        cast='Actor 1, Actor 2',
        description='A test movie description',
        poster='http://example.com/poster.jpg',
        tmdb_poster='http://example.com/tmdb_poster.jpg',
        poster_identifier='poster_id',
    )

    mock_movie_service.update_movie.return_value = valid_movie

    with TestClient(app) as client:
        response = client.patch(f'/movies/{movie_id}', json={'title': 'Updated'})

    assert response.status_code == 200, response.text
    # Check return body
    data = response.json()
    assert data['title'] == 'Updated'
    assert data['id'] == str(movie_id)


@pytest.mark.asyncio
async def test_update_movie_forbidden(app: FastAPI) -> None:
    """Test that update_movie requires update:movies scope."""
    movie_id = uuid.uuid4()

    # User only has read:movies
    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|123', email='test@test.com', permissions=['read:movies']
    )

    with TestClient(app) as client:
        response = client.patch(f'/movies/{movie_id}', json={'title': 'Updated'})

    assert response.status_code == 403
    assert 'User lacks required permissions' in response.text


@pytest.mark.asyncio
async def test_get_construct_items_success(app: FastAPI, mock_item_service: AsyncMock) -> None:
    """Test fetching construct items with read:constructs permission."""
    construct_id = uuid.uuid4()

    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|123', email='test@test.com', permissions=['read:constructs']
    )

    mock_item_service.get_items_for_owner_as_ordered_list.return_value = []

    with TestClient(app) as client:
        response = client.get(f'/constructs/{construct_id}/items')

    assert response.status_code == 200
