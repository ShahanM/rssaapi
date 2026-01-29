"""Tests for the study steps router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.study_components.study_steps import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import (
    StudyStepPageServiceDep,
    StudyStepServiceDep,
)


def override_dep(app, dep, mock) -> None:
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
def mock_step_service() -> AsyncMock:
    """Mocks the step service for testing."""
    return AsyncMock()


@pytest.fixture
def mock_page_service() -> AsyncMock:
    """Mocks the page service for testing."""
    return AsyncMock()


@pytest.fixture
def client(mock_step_service: AsyncMock, mock_page_service: AsyncMock) -> Generator[TestClient, None, None]:
    """Mocks the client for testing."""
    app = FastAPI()
    app.include_router(router)

    override_dep(app, StudyStepServiceDep, mock_step_service)
    override_dep(app, StudyStepPageServiceDep, mock_page_service)

    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(sub='auth0|user123', email='user@test.com', permissions=['admin:all'])

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    from rssa_api.auth.security import get_current_user
    from rssa_api.data.schemas.auth_schemas import UserSchema

    async def mock_current_user() -> UserSchema:
        return UserSchema(
            id=uuid.uuid4(),
            email='user@test.com',
            auth0_sub='auth0|user123',
            is_active=True,
            created_at='2021-01-01T00:00:00',
        )

    app.dependency_overrides[get_current_user] = mock_current_user

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_study_step(client: TestClient, mock_step_service: AsyncMock) -> None:
    """Tests the get study step endpoint."""
    step_id = uuid.uuid4()
    mock_step = MagicMock()
    mock_step.id = step_id
    mock_step.name = 'Step'
    mock_step.description = 'Desc'
    # Ensure step_type matches one of the allowed literals if enum?
    mock_step.step_type = 'instruction'
    mock_step.key = 'key'
    mock_step.order_position = 1
    mock_step.study_id = uuid.uuid4()
    mock_step.created_at = '2023-01-01'
    mock_step.updated_at = '2023-01-01'
    mock_step.enabled = True
    mock_step.is_active = True

    # Mock nested root_page_info
    mock_page_info = MagicMock()
    mock_page_info.data.title = 'Page Title'
    mock_page_info.data.instructions = 'Instructions'
    mock_page_info.data.page_type = 'default'
    mock_page_info.data.study_step_id = uuid.uuid4()
    mock_page_info.data.name = 'Page Name'
    mock_page_info.data.description = 'Page Desc'
    mock_page_info.data.study_id = uuid.uuid4()
    mock_page_info.data.id = uuid.uuid4()

    mock_page_info.next_id = uuid.uuid4()
    mock_page_info.next_path = '/next'

    mock_step.root_page_info = mock_page_info

    # Missing top-level fields
    mock_step.title = 'Step Title'
    mock_step.instructions = 'Step Instructions'
    mock_step.path = '/step/path'
    mock_step.survey_api_root = '/api/survey'

    mock_step_service.get.return_value = mock_step

    response = client.get(f'/steps/{step_id}')
    assert response.status_code == 200, response.text
    assert response.json()['name'] == 'Step'


@pytest.mark.asyncio
async def test_get_pages_for_study_step(client: TestClient, mock_page_service: AsyncMock) -> None:
    """Tests the get pages for study step endpoint."""
    step_id = uuid.uuid4()
    mock_page = MagicMock()
    mock_page.id = uuid.uuid4()
    mock_page.order_position = 1
    mock_page.name = 'Page 1'

    # router returns list[OrderedListItem], so mock needs to be compat
    mock_page_service.get_items_for_owner_as_ordered_list.return_value = [mock_page]

    response = client.get(f'/steps/{step_id}/pages')
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'Page 1'


@pytest.mark.asyncio
async def test_update_study_step(client: TestClient, mock_step_service: AsyncMock) -> None:
    """Tests the update study step endpoint."""
    step_id = uuid.uuid4()
    payload = {'name': 'Updated'}

    response = client.patch(f'/steps/{step_id}', json=payload)

    assert response.status_code == 204
    mock_step_service.update.assert_called_once()
