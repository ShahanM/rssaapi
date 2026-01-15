"""Tests for the study conditions router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.study_components.study_conditions import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import StudyConditionServiceDep


def override_dep(app, dep, mock):
    """Overrides a dependency in the application."""
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
def mock_condition_service() -> AsyncMock:
    """Mocks the condition service for testing."""
    return AsyncMock()


@pytest.fixture
def client(mock_condition_service: AsyncMock) -> Generator[TestClient, None, None]:
    """Mocks the client for testing."""
    app = FastAPI()
    app.include_router(router)
    override_dep(app, StudyConditionServiceDep, mock_condition_service)

    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(sub='auth0|user123', email='user@test.com', permissions=['admin:all'])

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_condition_detail(client: TestClient, mock_condition_service: AsyncMock) -> None:
    """Tests the get condition detail endpoint."""
    cond_id = uuid.uuid4()
    mock_cond = MagicMock()
    mock_cond.id = cond_id
    mock_cond.name = 'Cond'
    mock_cond.description = 'Desc'
    mock_cond.study_id = uuid.uuid4()
    mock_cond.created_at = '2023-01-01'
    mock_cond.updated_at = '2023-01-01'
    mock_cond.enabled = True
    mock_cond.condition_type = 'between-subjects'
    mock_cond.randomization_weight = 1.0
    mock_cond.max_participants = 100
    mock_cond.is_active = True
    mock_cond.condition_config = {}
    mock_cond.condition_key = 'key'
    mock_cond.condition_class = 'class'
    mock_cond.group_id = uuid.uuid4()
    mock_cond.recommender_key = 'rec_key'
    mock_cond.created_by_id = uuid.uuid4()
    mock_cond.short_code = 'SC'

    mock_condition_service.get.return_value = mock_cond

    response = client.get(f'/conditions/{cond_id}')
    assert response.status_code == 200, response.text
    assert response.json()['name'] == 'Cond'


@pytest.mark.asyncio
async def test_update_condition(client: TestClient, mock_condition_service: AsyncMock) -> None:
    """Tests the update condition endpoint."""
    cond_id = uuid.uuid4()
    payload = {'name': 'New Name'}

    mock_cond = MagicMock()
    mock_condition_service.get.return_value = mock_cond

    response = client.patch(f'/conditions/{cond_id}', json=payload)

    assert response.status_code == 204
    mock_condition_service.update.assert_called_once()
