"""Tests for the pages router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.pages import router
from rssa_api.auth.authorization import validate_api_key
from rssa_api.data.services.dependencies import StudyStepPageServiceDep
from rssa_api.data.services.study_components import StudyStepPageService


def get_dependency_key(annotated_dep: Any) -> Any:  # noqa: ANN401
    """Extracts the dependency function from an Annotated dependency."""
    for item in get_args(annotated_dep):
        if isinstance(item, FastAPI_Depends):
            return item.dependency
    raise ValueError(f'Could not find Depends in {annotated_dep}')


@pytest.fixture
def mock_page_service() -> AsyncMock:
    """Fixture for mocked StudyStepPageService."""
    return AsyncMock(spec=StudyStepPageService)


@pytest.fixture
def client(
    mock_page_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_dependency_key(StudyStepPageServiceDep)] = lambda: mock_page_service

    # Mock Auth usually returns study_id
    study_id = uuid.UUID('7a878158-2eff-476f-919d-5778667ce68d')

    async def mock_auth() -> uuid.UUID:
        return study_id

    app.dependency_overrides[validate_api_key] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_step_page_details_success(client: TestClient, mock_page_service: AsyncMock) -> None:
    """Test retrieving page details successfully."""
    page_id = uuid.uuid4()
    study_id = uuid.UUID('7a878158-2eff-476f-919d-5778667ce68d')
    step_id = uuid.uuid4()

    mock_page = MagicMock()
    mock_page.id = page_id
    mock_page.study_id = study_id
    mock_page.name = 'Page'
    mock_page.description = 'Desc'
    mock_page.page_type = 'survey'
    mock_page.study_step_id = step_id
    mock_page.order_position = 1
    mock_page.title = 'Page Title'
    mock_page.instructions = 'Instructions'
    mock_page.study_step_page_contents = []

    mock_page_service.get_with_navigation.return_value = {'current': mock_page, 'next_id': None, 'next_path': None}

    response = client.get(f'/pages/{page_id}')

    # Assert
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['data']['id'] == str(page_id)


@pytest.mark.asyncio
async def test_get_step_page_details_not_found(client: TestClient, mock_page_service: AsyncMock) -> None:
    """Test page retrieval when page is not found."""
    page_id = uuid.uuid4()

    mock_page_service.get_with_navigation.return_value = None

    response = client.get(f'/pages/{page_id}')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Page was not found, study configuration fault.'


@pytest.mark.asyncio
async def test_get_step_page_details_forbidden(client: TestClient, mock_page_service: AsyncMock) -> None:
    """Test usage of page from different study."""
    page_id = uuid.uuid4()
    other_study_id = uuid.uuid4()
    step_id = uuid.uuid4()

    mock_page = MagicMock()
    mock_page.id = page_id
    mock_page.study_id = other_study_id  # Mismatch
    mock_page.name = 'Page'
    mock_page.description = 'Desc'
    mock_page.page_type = 'survey'
    mock_page.study_step_id = step_id
    mock_page.order_position = 1
    mock_page.title = 'Page Title'
    mock_page.instructions = 'Instructions'
    mock_page.study_step_page_contents = []

    mock_page_service.get_with_navigation.return_value = {'current': mock_page, 'next_id': None, 'next_path': None}

    response = client.get(f'/pages/{page_id}')

    assert response.status_code == 403
    assert response.json()['detail'] == 'Step not valid for this study.'
