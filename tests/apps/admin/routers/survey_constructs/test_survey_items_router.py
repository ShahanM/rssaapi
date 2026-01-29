"""Tests for the survey items router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.survey_constructs.survey_items import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import SurveyItemServiceDep


# Helper to override dependency
def override_dep(app, dep, mock) -> None:
    """Helper to override dependency."""
    from typing import get_args

    from fastapi.params import Depends as FastAPI_Depends

    dep_callable = None
    for item in get_args(dep):
        if isinstance(item, FastAPI_Depends):
            dep_callable = item.dependency
            break

    if dep_callable:
        app.dependency_overrides[dep_callable] = lambda: mock
    else:
        app.dependency_overrides[dep] = lambda: mock


@pytest.fixture
def mock_item_service() -> AsyncMock:
    """Mock item service."""
    return AsyncMock()


@pytest.fixture
def client(
    mock_item_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    override_dep(app, SurveyItemServiceDep, mock_item_service)

    # Mock Auth0 user
    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(
            sub='auth0|user123',
            email='user@test.com',
            permissions=['admin:all', 'read:items', 'update:items', 'delete:items'],
        )

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_item(client: TestClient, mock_item_service: AsyncMock) -> None:
    """Test retrieving a survey item by ID."""
    item_id = uuid.uuid4()

    mock_item = MagicMock()
    mock_item.id = item_id
    mock_item.text = 'Item Text'
    mock_item.survey_construct_id = uuid.uuid4()
    mock_item.created_at = '2023-01-01'
    mock_item.updated_at = '2023-01-01'
    mock_item.order_position = 1

    mock_item_service.get.return_value = mock_item

    response = client.get(f'/items/{item_id}')

    assert response.status_code == 200
    assert response.json()['text'] == 'Item Text'
    mock_item_service.get.assert_called_once_with(item_id)


def test_update_item(client: TestClient, mock_item_service: AsyncMock) -> None:
    """Test updating a survey item."""
    item_id = uuid.uuid4()
    payload = {'text': 'Updated Item Text'}

    response = client.patch(f'/items/{item_id}', json=payload)

    assert response.status_code == 204
    mock_item_service.update.assert_called_once_with(item_id, payload)


def test_delete_item(client: TestClient, mock_item_service: AsyncMock) -> None:
    """Test deleting a survey item."""
    item_id = uuid.uuid4()

    response = client.delete(f'/items/{item_id}')

    assert response.status_code == 204
    mock_item_service.delete.assert_called_once_with(item_id)
