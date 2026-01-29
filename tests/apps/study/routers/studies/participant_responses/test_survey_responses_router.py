"""Tests for the survey responses router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.participant_responses.survey_responses import survey_router
from rssa_api.auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from rssa_api.data.schemas.participant_schemas import StudyParticipantRead
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
    app.include_router(survey_router)

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
async def test_create_survey_response_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test creating a survey response successfully."""
    step_id = uuid.uuid4()

    payload = {
        'study_step_id': str(step_id),
        'context_tag': 'survey',
        'survey_construct_id': str(uuid.uuid4()),
        'survey_item_id': str(uuid.uuid4()),
        'survey_scale_id': str(uuid.uuid4()),
        'survey_scale_level_id': str(uuid.uuid4()),
    }

    # Mock return
    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_step_id = step_id
    mock_res.context_tag = 'survey'
    mock_res.study_step_page_id = None

    mock_res.survey_construct_id = uuid.UUID(payload['survey_construct_id'])
    mock_res.survey_item_id = uuid.UUID(payload['survey_item_id'])
    mock_res.survey_scale_id = uuid.UUID(payload['survey_scale_id'])
    mock_res.survey_scale_level_id = uuid.UUID(payload['survey_scale_level_id'])

    mock_res.created_at = '2023-01-01T00:00:00Z'
    mock_res.updated_at = '2023-01-01T00:00:00Z'
    mock_res.version = 1  # VersionMixin says version: int

    mock_response_service.create_response = AsyncMock(return_value=mock_res)

    response = client.post('/survey/', json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data['survey_construct_id'] == payload['survey_construct_id']


@pytest.mark.asyncio
async def test_get_survey_response_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test retrieving survey responses."""
    page_id = uuid.uuid4()

    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_step_id = uuid.uuid4()
    mock_res.context_tag = 'survey'
    mock_res.study_step_page_id = page_id

    mock_res.survey_construct_id = uuid.uuid4()
    mock_res.survey_item_id = uuid.uuid4()
    mock_res.survey_scale_id = uuid.uuid4()
    mock_res.survey_scale_level_id = uuid.uuid4()

    mock_res.created_at = '2023-01-01T00:00:00Z'
    mock_res.updated_at = '2023-01-01T00:00:00Z'
    mock_res.version = 1

    mock_response_service.get_response_for_page = AsyncMock(return_value=[mock_res])

    response = client.get(f'/survey/{page_id}')

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]['context_tag'] == 'survey'


@pytest.mark.asyncio
async def test_update_survey_response_success(client: TestClient, mock_response_service: AsyncMock) -> None:
    """Test updating a survey response."""
    response_id = uuid.uuid4()
    version = 1
    new_level_id = uuid.uuid4()

    payload = {
        'id': str(response_id),
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-01-01T00:00:00Z',
        'context_tag': 'survey',
        'study_step_id': str(uuid.uuid4()),  # Required in Update schema due to inheritance from Read/Base
        'survey_construct_id': str(uuid.uuid4()),
        'survey_item_id': str(uuid.uuid4()),
        'survey_scale_id': str(uuid.uuid4()),
        'survey_scale_level_id': str(new_level_id),
        'version': version,
    }

    mock_response_service.update_response = AsyncMock(return_value=True)

    response = client.patch(f'/survey/{response_id}', json=payload)

    assert response.status_code == 204, response.text
    mock_response_service.update_response.assert_called_once()
    args, kwargs = mock_response_service.update_response.call_args
    assert args[0] == ResponseType.SURVEY_ITEM
    assert args[2]['survey_scale_level_id'] == new_level_id
