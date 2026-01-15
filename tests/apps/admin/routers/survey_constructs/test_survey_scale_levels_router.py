"""Tests for the survey scale levels router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.survey_constructs.survey_scale_levels import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import SurveyScaleLevelServiceDep


# Helper to override dependency
def override_dep(app, dep, mock):
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
def mock_level_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(
    mock_level_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    override_dep(app, SurveyScaleLevelServiceDep, mock_level_service)

    # Mock Auth0 user
    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(sub='auth0|user123', email='user@test.com', permissions=['admin:all'])

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_delete_scale_level(client: TestClient, mock_level_service: AsyncMock):
    """Test deleting a scale level."""
    level_id = uuid.uuid4()

    response = client.delete(f'/levels/{level_id}')

    assert response.status_code == 204
    mock_level_service.delete.assert_called_once_with(level_id)
