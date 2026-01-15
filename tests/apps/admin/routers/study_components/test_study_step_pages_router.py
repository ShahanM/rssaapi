"""Tests for the study step pages router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.study_components.study_step_pages import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import (
    StudyStepPageContentServiceDep,
    StudyStepPageServiceDep,
)


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
def mock_page_service() -> AsyncMock:
    """Mocks the page service for testing."""
    return AsyncMock()


@pytest.fixture
def mock_content_service() -> AsyncMock:
    """Mocks the content service for testing."""
    return AsyncMock()


@pytest.fixture
def client(mock_page_service: AsyncMock, mock_content_service: AsyncMock) -> Generator[TestClient, None, None]:
    """Mocks the client for testing."""
    app = FastAPI()
    app.include_router(router)
    override_dep(app, StudyStepPageServiceDep, mock_page_service)
    override_dep(app, StudyStepPageContentServiceDep, mock_content_service)

    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(sub='auth0|user123', email='user@test.com', permissions=['admin:all'])

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_page_details(client: TestClient, mock_page_service: AsyncMock) -> None:
    """Tests the get page details endpoint."""
    page_id = uuid.uuid4()
    mock_page = MagicMock()
    mock_page.id = page_id
    mock_page.name = 'Page'
    mock_page.description = 'Desc'
    mock_page.study_step_id = uuid.uuid4()
    mock_page.created_at = '2023-01-01'
    mock_page.updated_at = '2023-01-01'
    mock_page.order_position = 1
    mock_page.page_type = 'default'
    mock_page.title = 'Title'
    mock_page.instructions = 'Inst'
    mock_page.enabled = True
    mock_page.study_id = uuid.uuid4()

    mock_page_service.get_detailed.return_value = mock_page

    response = client.get(f'/pages/{page_id}')
    assert response.status_code == 200
    assert response.json()['name'] == 'Page'


@pytest.mark.asyncio
async def test_update_page(client: TestClient, mock_page_service: AsyncMock) -> None:
    """Tests the update page endpoint."""
    page_id = uuid.uuid4()
    payload = {'name': 'Updated'}
    response = client.patch(f'/pages/{page_id}', json=payload)
    assert response.status_code == 204
    mock_page_service.update.assert_called_once()


@pytest.mark.asyncio
async def test_get_page_content(client: TestClient, mock_content_service: AsyncMock) -> None:
    """Tests the get page content endpoint."""
    page_id = uuid.uuid4()
    mock_content = MagicMock()
    mock_content.id = uuid.uuid4()
    mock_content.order_position = 1
    mock_content.name = 'Content Item'

    mock_content_service.get_items_for_owner_as_ordered_list.return_value = [mock_content]

    response = client.get(f'/pages/{page_id}/contents')
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'Content Item'
