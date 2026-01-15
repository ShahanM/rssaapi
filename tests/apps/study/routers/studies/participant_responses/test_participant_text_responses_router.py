"""Tests for the participant text responses router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.participant_responses.participant_text_responses import text_response_router
from rssa_api.auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from rssa_api.data.schemas.participant_schemas import StudyParticipantRead
from rssa_api.data.services import ResponseType
from rssa_api.data.services.dependencies import ParticipantResponseServiceDep
from rssa_api.data.services.response_service import ParticipantResponseService


def get_dependency_key(annotated_dep: Any) -> Any:
    """Extracts the dependency function from an Annotated dependency."""
    for item in get_args(annotated_dep):
        if isinstance(item, FastAPI_Depends):
            return item.dependency
    raise ValueError(f'Could not find Depends in {annotated_dep}')


@pytest.fixture
def mock_response_service() -> AsyncMock:
    """Fixture for mocked ParticipantResponseService."""
    return AsyncMock(spec=ParticipantResponseService)


@pytest.fixture
def client(
    mock_response_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(text_response_router)

    app.dependency_overrides[get_dependency_key(ParticipantResponseServiceDep)] = lambda: mock_response_service

    # Mock Auth
    async def mock_validate_participant() -> dict[str, uuid.UUID]:
        return {'pid': uuid.uuid4(), 'sid': uuid.uuid4()}

    app.dependency_overrides[validate_study_participant] = mock_validate_participant

    # Mock extra dependencies in router decorator
    app.dependency_overrides[validate_api_key] = lambda: uuid.uuid4()
    app.dependency_overrides[get_current_participant] = lambda: MagicMock(spec=StudyParticipantRead)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_text_response_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test creating a text response successfully."""
    step_id = uuid.uuid4()

    payload = {'study_step_id': str(step_id), 'context_tag': 'feedback_box', 'response_text': 'This is my feedback'}

    # Mock return
    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_step_id = step_id
    mock_res.context_tag = 'feedback_box'
    mock_res.response_text = 'This is my feedback'
    mock_res.study_step_page_id = None

    mock_res.created_at = '2023-01-01T00:00:00Z'
    mock_res.updated_at = '2023-01-01T00:00:00Z'
    mock_res.version_id = uuid.uuid4()

    mock_response_service.create_response = AsyncMock(return_value=mock_res)

    response = client.post('/texts/', json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data['response_text'] == 'This is my feedback'


@pytest.mark.asyncio
async def test_get_text_response_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test retrieving text responses."""
    page_id = uuid.uuid4()

    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_step_id = uuid.uuid4()
    mock_res.context_tag = 'feedback_box'
    mock_res.response_text = 'Some text'
    mock_res.study_step_page_id = page_id

    mock_res.created_at = '2023-01-01T00:00:00Z'
    mock_res.updated_at = '2023-01-01T00:00:00Z'
    mock_res.version_id = uuid.uuid4()

    mock_response_service.get_response_for_page = AsyncMock(return_value=[mock_res])

    response = client.get(f'/texts/?page_id={page_id}')

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]['response_text'] == 'Some text'


@pytest.mark.asyncio
async def test_update_text_response_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test updating a text response."""
    response_id = uuid.uuid4()
    version = 1

    payload = {
        'id': str(response_id),
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-01-01T00:00:00Z',
        'response_text': 'Updated text',
        'study_step_id': str(uuid.uuid4()),  # Required by Read schema inheritance?
        'context_tag': 'tag',
        'survey_construct_id': str(uuid.uuid4()),  # Wait, text response doesn't have create fields in update?
        # Update inherits Read. Read inherits Base. Base has context fields.
        'version': version,
    }

    # ParticipantFreeformResponseUpdate inherits Read.
    # Read inherits Base, VersionMixin, DBMixin.
    # Base inherits ParticipantResponseContextMixin.
    # So Update schema DOES have study_step_id and context_tag and response_text!

    mock_response_service.update_response = AsyncMock(return_value=True)

    response = client.patch(f'/texts/{response_id}', json=payload)

    assert response.status_code == 204, response.text
    mock_response_service.update_response.assert_called_once()
    args, kwargs = mock_response_service.update_response.call_args
    assert args[0] == ResponseType.TEXT_RESPONSE
    assert args[2]['response_text'] == 'Updated text'
