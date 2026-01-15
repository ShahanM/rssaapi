"""Tests for the participant interaction responses router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.participant_responses.participant_interactions import interactions_router
from rssa_api.auth.authorization import validate_study_participant
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
    app.include_router(interactions_router)

    app.dependency_overrides[get_dependency_key(ParticipantResponseServiceDep)] = lambda: mock_response_service

    # Mock Auth
    async def mock_validate_participant() -> dict[str, uuid.UUID]:
        return {'pid': uuid.uuid4(), 'sid': uuid.uuid4()}

    app.dependency_overrides[validate_study_participant] = mock_validate_participant

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_interaction_response_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test creating an interaction response successfully."""
    step_id = uuid.uuid4()
    payload = {
        'study_step_id': str(step_id),
        'context_tag': 'tag',
        'payload_json': {'experimnet_condition': 'A', 'extra': {'foo': 'bar'}},
    }

    # Mock return
    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_step_id = step_id
    mock_res.context_tag = 'tag'
    mock_res.study_step_page_id = None

    mock_payload = MagicMock()
    mock_payload.experimnet_condition = 'A'
    mock_payload.extra = {'foo': 'bar'}
    mock_res.payload_json = mock_payload
    mock_res.created_at = '2023-01-01T00:00:00Z'
    mock_res.updated_at = '2023-01-01T00:00:00Z'
    mock_res.version_id = uuid.uuid4()

    # create_response returns the object directly
    mock_response_service.create_response = AsyncMock(return_value=mock_res)

    response = client.post('/interactions/', json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data['context_tag'] == 'tag'
    assert data['payload_json']['experimnet_condition'] == 'A'


@pytest.mark.asyncio
async def test_get_interaction_responses_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test retrieving interaction responses."""
    step_id = uuid.uuid4()

    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_step_id = step_id
    mock_res.context_tag = 'tag'
    mock_res.study_step_page_id = None

    mock_payload = MagicMock()
    mock_payload.experimnet_condition = 'A'
    mock_payload.extra = {}
    mock_res.payload_json = mock_payload
    mock_res.created_at = '2023-01-01T00:00:00Z'
    mock_res.updated_at = '2023-01-01T00:00:00Z'
    mock_res.version_id = uuid.uuid4()

    mock_response_service.get_response_for_step = AsyncMock(return_value=[mock_res])

    response = client.get(f'/interactions/{step_id}')

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['context_tag'] == 'tag'


@pytest.mark.asyncio
async def test_update_interaction_response_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test updating an interaction response."""
    interaction_id = uuid.uuid4()
    version = 1

    payload = {
        'id': str(interaction_id),
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-01-01T00:00:00Z',
        'payload_json': {'experimnet_condition': 'B', 'extra': {'baz': 'qux'}},
        'version': version,
    }

    # Only fields in ParticipantStudyInteractionResponseUpdate
    # which inherits ParticipantStudyInteractionResponseBase, DBMixin, VersionMixin
    # Base has payload_json.

    mock_response_service.update_response = AsyncMock(return_value=True)

    response = client.patch(f'/interactions/{interaction_id}', json=payload)

    assert response.status_code == 204, response.text
    mock_response_service.update_response.assert_called_once()
    args, kwargs = mock_response_service.update_response.call_args
    assert args[0] == ResponseType.STUDY_INTERACTION
    assert args[1] == interaction_id
    assert args[2]['payload_json']['experimnet_condition'] == 'B'
    assert args[3] == version


@pytest.mark.asyncio
async def test_update_interaction_response_conflict(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test updating interaction response conflict."""
    interaction_id = uuid.uuid4()
    version = 1

    payload = {
        'id': str(interaction_id),
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-01-01T00:00:00Z',
        'payload_json': {'experimnet_condition': 'B', 'extra': {}},
        'version': version,
    }

    mock_response_service.update_response = AsyncMock(return_value=False)

    response = client.patch(f'/interactions/{interaction_id}', json=payload)

    assert response.status_code == 409
    assert response.json()['detail'] == 'Resource version mismatch. Data was updated by another process'
