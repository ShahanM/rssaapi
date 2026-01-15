"""Tests for the feedback router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.feedback import router
from rssa_api.auth.authorization import get_current_participant, validate_api_key
from rssa_api.data.schemas.participant_schemas import StudyParticipantRead
from rssa_api.data.services.dependencies import FeedbackServiceDep
from rssa_api.data.services.study_participants import FeedbackService


def get_dependency_key(annotated_dep: Any) -> Any:
    """Extracts the dependency function from an Annotated dependency."""
    for item in get_args(annotated_dep):
        if isinstance(item, FastAPI_Depends):
            return item.dependency
    raise ValueError(f'Could not find Depends in {annotated_dep}')


@pytest.fixture
def mock_feedback_service() -> AsyncMock:
    """Fixture for mocked FeedbackService."""
    return AsyncMock(spec=FeedbackService)


@pytest.fixture
def client(
    mock_feedback_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_dependency_key(FeedbackServiceDep)] = lambda: mock_feedback_service

    # Mock Auth
    study_id = uuid.UUID('7a878158-2eff-476f-919d-5778667ce68d')

    async def mock_api_key_auth() -> uuid.UUID:
        return study_id

    app.dependency_overrides[validate_api_key] = mock_api_key_auth

    async def mock_get_participant() -> StudyParticipantRead:
        p = MagicMock(spec=StudyParticipantRead)
        p.id = uuid.uuid4()
        p.study_id = study_id
        return p

    app.dependency_overrides[get_current_participant] = mock_get_participant

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_feedback_success(client: TestClient, mock_feedback_service: AsyncMock) -> None:
    """Test creating feedback successfully."""
    step_id = uuid.uuid4()
    payload = {
        'feedback_text': 'Great study!',
        'feedback_type': 'general',
        'feedback_category': 'praise',
        'study_step_id': str(step_id),
        'context_tag': 'survey',
    }

    # Mock return
    mock_feedback = MagicMock()
    mock_feedback.id = uuid.uuid4()
    mock_feedback.study_id = uuid.uuid4()
    mock_feedback.participant_id = uuid.uuid4()
    mock_feedback.feedback_text = 'Great study!'
    mock_feedback.feedback_type = 'general'
    mock_feedback.feedback_category = 'praise'
    mock_feedback.study_step_id = step_id
    mock_feedback.context_tag = 'survey'
    mock_feedback.study_step_page_id = None
    mock_feedback.created_at = '2023-01-01T00:00:00Z'
    mock_feedback.updated_at = '2023-01-01T00:00:00Z'
    mock_feedback.version_id = uuid.uuid4()

    mock_feedback_service.create_feedback.return_value = mock_feedback

    response = client.post('/feedbacks/', json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data['feedback_text'] == 'Great study!'


@pytest.mark.asyncio
async def test_update_feedback_success(client: TestClient, mock_feedback_service: AsyncMock) -> None:
    """Test updating feedback successfully."""
    feedback_id = uuid.uuid4()
    step_id = uuid.uuid4()
    payload = {
        'feedback_text': 'Updated message',
        'feedback_type': 'bug',
        'feedback_category': 'ui',
        'study_step_id': str(step_id),
        'context_tag': 'survey',
    }

    mock_feedback_service.update.return_value = None

    response = client.patch(f'/feedbacks/{feedback_id}', json=payload)

    assert response.status_code == 204
    mock_feedback_service.update.assert_called_once()
    args, kwargs = mock_feedback_service.update.call_args
    assert args[0] == feedback_id
    assert args[1]['feedback_text'] == 'Updated message'
