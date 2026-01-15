"""Tests for the steps router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.steps import router
from rssa_api.auth.authorization import validate_api_key
from rssa_api.data.services.dependencies import StudyStepPageServiceDep, StudyStepServiceDep
from rssa_api.data.services.study_components import (
    StudyStepPageService,
    StudyStepService,
)


def get_dependency_key(annotated_dep: Any) -> Any:
    """Extracts the dependency function from an Annotated dependency."""
    for item in get_args(annotated_dep):
        if isinstance(item, FastAPI_Depends):
            return item.dependency
    raise ValueError(f'Could not find Depends in {annotated_dep}')


@pytest.fixture
def mock_step_service() -> AsyncMock:
    """Fixture for mocked StudyStepService."""
    return AsyncMock(spec=StudyStepService)


@pytest.fixture
def mock_page_service() -> AsyncMock:
    """Fixture for mocked StudyStepPageService."""
    return AsyncMock(spec=StudyStepPageService)


@pytest.fixture
def client(
    mock_step_service: AsyncMock,
    mock_page_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_dependency_key(StudyStepServiceDep)] = lambda: mock_step_service
    app.dependency_overrides[get_dependency_key(StudyStepPageServiceDep)] = lambda: mock_page_service

    # Mock Auth - returns a study_id
    # We'll rely on the test to set up matching study_ids in mocks
    study_id = uuid.UUID('7a878158-2eff-476f-919d-5778667ce68d')

    async def mock_auth() -> uuid.UUID:
        return study_id

    app.dependency_overrides[validate_api_key] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_study_step_success(
    client: TestClient, mock_step_service: AsyncMock, mock_page_service: AsyncMock
) -> None:
    """Test retrieving a study step successfully."""
    step_id = uuid.uuid4()
    study_id = uuid.UUID('7a878158-2eff-476f-919d-5778667ce68d')  # Matches mock_auth

    mock_step = MagicMock()
    mock_step.id = step_id
    mock_step.study_id = study_id
    mock_step.name = 'Step'
    mock_step.description = 'Desc'
    mock_step.path = '/path'
    mock_step.step_type = 'consent'
    mock_step.title = 'Title'
    mock_step.instructions = 'Instructions'
    mock_step.survey_api_root = None
    mock_step.root_page_info = None  # This is NavigationWrapper | None.
    # If using None, ensure Schema allows None. Schema: root_page_info: NavigationWrapper[StudyStepPageRead] | None = None

    # Mocking get_with_navigation returns dict wrapper
    mock_step_service.get_with_navigation.return_value = {
        'current': mock_step,
        'next_id': uuid.uuid4(),
        'next_path': '/next',
    }

    # Mock page service for root_page_info logic
    mock_page_service.get_first_with_navigation.return_value = None

    response = client.get(f'/steps/{step_id}')

    assert response.status_code == 200, response.text
    data = response.json()
    assert data['data']['id'] == str(step_id)


@pytest.mark.asyncio
async def test_get_study_step_forbidden(
    client: TestClient,
    mock_step_service: AsyncMock,
) -> None:
    """Test forbidden access when study_id mismatches."""
    step_id = uuid.uuid4()
    other_study_id = uuid.uuid4()

    mock_step = MagicMock()
    mock_step.id = step_id
    mock_step.study_id = other_study_id  # Mismatch
    mock_step.name = 'Step'
    mock_step.description = 'Desc'
    mock_step.path = '/path'
    mock_step.step_type = 'consent'
    mock_step.title = None
    mock_step.instructions = None
    mock_step.root_page_info = None
    mock_step.survey_api_root = None

    mock_step_service.get_with_navigation.return_value = {'current': mock_step, 'next_id': None, 'next_path': None}

    response = client.get(f'/steps/{step_id}')

    assert response.status_code == 403
    assert response.json()['detail'] == 'Study step does not belong to the authorized study.'


@pytest.mark.asyncio
async def test_get_first_page_endpoint_success(client: TestClient, mock_page_service: AsyncMock) -> None:
    """Test retrieving the first page of a step."""
    step_id = uuid.uuid4()
    page_id = uuid.uuid4()
    study_id = uuid.UUID('7a878158-2eff-476f-919d-5778667ce68d')

    mock_page = MagicMock()
    mock_page.id = page_id
    mock_page.study_id = study_id
    mock_page.name = 'Page'
    mock_page.description = 'Desc'
    mock_page.page_type = 'survey'
    mock_page.study_step_id = step_id
    mock_page.order_position = 1
    mock_page.study_step_page_contents = []
    mock_page.title = 'Page Title'
    mock_page.instructions = 'Instructions'

    mock_page_service.get_first_with_navigation.return_value = {
        'current': mock_page,
        'next_id': None,
        'next_path': None,
    }

    response = client.get(f'/steps/{step_id}/pages/first')

    assert response.status_code == 200
    mock_page_service.get_first_with_navigation.assert_called_once_with(step_id)
