"""Tests for the users router."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.users import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    # Mock Auth0 user
    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(sub='auth0|user123', email='user@test.com', permissions=['admin:all', 'read:users'])

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth0_mgmt():
    """Fixture to mock auth0 management calls."""
    with (
        patch('rssa_api.apps.admin.routers.users.get_user_profile_by_id', new_callable=AsyncMock) as mock_get,
        patch('rssa_api.apps.admin.routers.users.search_users', new_callable=AsyncMock) as mock_search,
    ):
        yield mock_get, mock_search


@pytest.mark.asyncio
async def test_get_user_profile_endpoint_success(client: TestClient, mock_auth0_mgmt) -> None:
    """Test retrieving a user profile successfully."""
    mock_get, _ = mock_auth0_mgmt
    mock_get.return_value = {'user_id': 'uid', 'email': 'test@test.com'}

    response = client.get('/users/uid/profile')

    assert response.status_code == 200
    assert response.json()['email'] == 'test@test.com'
    mock_get.assert_called_once_with('uid')


@pytest.mark.asyncio
async def test_get_user_profile_not_found(client: TestClient, mock_auth0_mgmt) -> None:
    """Test retrieving a user profile that doesn't exist."""
    mock_get, _ = mock_auth0_mgmt
    mock_get.return_value = None

    response = client.get('/users/uid/profile')

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_permissions(client: TestClient, mock_auth0_mgmt) -> None:
    """Test retrieving user permissions."""
    mock_get, _ = mock_auth0_mgmt
    mock_get.return_value = {'permissions': ['read:all']}

    response = client.get('/users/uid/permissions')

    assert response.status_code == 200
    assert response.json()['permissions'] == ['read:all']


@pytest.mark.asyncio
async def test_search_users_endpoint(client: TestClient, mock_auth0_mgmt) -> None:
    """Test searching users."""
    _, mock_search = mock_auth0_mgmt
    mock_search.return_value = {'users': [], 'total': 0}

    response = client.get('/users/?q=test')

    assert response.status_code == 200
    mock_search.assert_called_once_with(search_query='test', page=0, per_page=20)
