"""Tests for the study step page contents router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.study_components.study_step_page_contents import (
    router,
)
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import StudyStepPageContentServiceDep


def override_dep(app, dep, mock):
    """Override a dependency in the app."""
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
def mock_content_service() -> AsyncMock:
    """Fixture for a mock content service."""
    return AsyncMock()


@pytest.fixture
def client(mock_content_service: AsyncMock) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)
    override_dep(app, StudyStepPageContentServiceDep, mock_content_service)

    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(
            sub='auth0|user123', email='user@test.com', permissions=['admin:all', 'delete:content', 'update:content']
        )

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_page_content(client: TestClient, mock_content_service: AsyncMock) -> None:
    """Test updating a page content."""
    content_id = uuid.uuid4()
    payload = {'order_position': 2}

    response = client.patch(f'/contents/{content_id}', json=payload)

    assert response.status_code == 204
    mock_content_service.update.assert_called_once()


@pytest.mark.asyncio
async def test_remove_content(client: TestClient, mock_content_service: AsyncMock) -> None:
    """Test removing a page content."""
    content_id = uuid.uuid4()
    response = client.delete(f'/contents/{content_id}')
    assert response.status_code == 204
    mock_content_service.delete.assert_called_once_with(content_id)
