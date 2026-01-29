"""Tests for the participant ratings router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.participant_responses.participant_ratings import ratings_router
from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.services import ResponseType
from rssa_api.data.services.dependencies import ParticipantResponseServiceDep
from rssa_api.data.services.response_service import ParticipantResponseService


def get_dependency_key(annotated_dep: Any) -> Any:  # noqa: ANN401
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
    app.include_router(ratings_router)

    app.dependency_overrides[get_dependency_key(ParticipantResponseServiceDep)] = lambda: mock_response_service

    # Mock Auth
    async def mock_validate_participant() -> dict[str, uuid.UUID]:
        return {'pid': uuid.uuid4(), 'sid': uuid.uuid4()}

    app.dependency_overrides[validate_study_participant] = mock_validate_participant

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_rating_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test creating a rating successfully."""
    step_id = uuid.uuid4()
    item_id = uuid.uuid4()

    payload = {
        'study_step_id': str(step_id),
        'context_tag': 'rating_task',
        'rated_item': {'item_id': str(item_id), 'rating': 5},
    }

    # Mock return
    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_step_id = step_id
    mock_res.context_tag = 'rating_task'
    mock_res.study_step_page_id = None

    mock_rated_item = MagicMock()
    mock_rated_item.item_id = item_id
    mock_rated_item.rating = 5
    mock_res.rated_item = mock_rated_item

    mock_res.created_at = '2023-01-01T00:00:00Z'
    mock_res.updated_at = '2023-01-01T00:00:00Z'
    mock_res.version_id = uuid.uuid4()

    mock_response_service.create_response = AsyncMock(return_value=mock_res)

    response = client.post('/ratings/', json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data['rated_item']['rating'] == 5


@pytest.mark.asyncio
async def test_get_ratings_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test retrieving ratings."""
    page_id = uuid.uuid4()

    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_step_id = uuid.uuid4()
    mock_res.context_tag = 'rating_task'
    mock_res.study_step_page_id = page_id

    # ... (existing content)

    mock_rated_item = MagicMock()
    mock_rated_item.item_id = uuid.uuid4()
    mock_rated_item.rating = 4
    mock_res.rated_item = mock_rated_item

    mock_res.created_at = '2023-01-01T00:00:00Z'
    mock_res.updated_at = '2023-01-01T00:00:00Z'
    mock_res.version_id = uuid.uuid4()

    mock_response_service.get_response_for_page = AsyncMock(return_value=[mock_res])

    response = client.get(f'/ratings/?page_id={page_id}')

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]['rated_item']['rating'] == 4


@pytest.mark.asyncio
async def test_update_rating_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test updating a rating."""
    rating_id = uuid.uuid4()
    version = 1
    item_id = uuid.uuid4()

    payload = {
        'id': str(rating_id),
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-01-01T00:00:00Z',
        'rated_item': {'item_id': str(item_id), 'rating': 3},
        'version': version,
    }

    mock_response_service.update_response = AsyncMock(return_value=True)

    response = client.patch(f'/ratings/{rating_id}', json=payload)

    assert response.status_code == 204, response.text
    mock_response_service.update_response.assert_called_once()
    args, kwargs = mock_response_service.update_response.call_args
    assert args[0] == ResponseType.CONTENT_RATING
    assert args[2]['rating'] == 3
    # Check flattening logic: item_id and rating should be in update_data
    assert args[2]['item_id'] == item_id
