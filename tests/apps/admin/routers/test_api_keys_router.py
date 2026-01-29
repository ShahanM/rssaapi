"""Tests for the API keys router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.api_keys import router
from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.data.services.dependencies import ApiKeyServiceDep
from rssa_api.data.services.study_admin import ApiKeyService


@pytest.fixture
def mock_apikey_service() -> AsyncMock:
    """Fixture for a mocked ApiKeyService."""
    return AsyncMock(spec=ApiKeyService)


@pytest.fixture
def client(mock_apikey_service: AsyncMock) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    from typing import get_args

    from fastapi.params import Depends as FastAPI_Depends

    # Extract the actual dependency callable from Annotated
    dep_callable = None
    for item in get_args(ApiKeyServiceDep):
        if isinstance(item, FastAPI_Depends):
            dep_callable = item.dependency
            break

    if dep_callable:
        app.dependency_overrides[dep_callable] = lambda: mock_apikey_service
    else:
        app.dependency_overrides[ApiKeyServiceDep] = lambda: mock_apikey_service

    # Mock Auth0 user
    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(sub='auth0|user123', email='user@test.com', permissions=['admin:all'])

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    async def mock_current_user() -> UserSchema:
        return UserSchema(
            id=uuid.uuid4(),
            email='user@test.com',
            auth0_sub='auth0|user123',
            is_active=True,
            created_at='2021-01-01T00:00:00',
        )

    app.dependency_overrides[get_current_user] = mock_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_api_keys_success(client: TestClient, mock_apikey_service: AsyncMock) -> None:
    """Test retrieving API keys successfully."""
    study_id = uuid.uuid4()

    # Use MagicMock or SimpleNamespace to avoid scope issues with class definitions
    mock_key = MagicMock()
    mock_key.id = uuid.uuid4()
    mock_key.study_id = study_id
    mock_key.user_id = uuid.uuid4()
    mock_key.description = 'Test Key'
    mock_key.plain_text_key = 'test-secret-key'
    mock_key.created_at = '2023-01-01T00:00:00Z'

    mock_apikey_service.get_api_keys_for_study.return_value = [mock_key]

    response = client.get(f'/api-keys/?study_id={study_id}')

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['description'] == 'Test Key'
    mock_apikey_service.get_api_keys_for_study.assert_called_once()
