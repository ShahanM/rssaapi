"""Tests for the recommendations router."""

import uuid
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.recommendations import router
from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.schemas.recommendations import EnrichedResponseWrapper
from rssa_api.services.dependencies import get_recommender_service
from rssa_api.services.recommender_service import RecommenderService


@pytest.fixture
def mock_recommender_service() -> AsyncMock:
    """Fixture for a mocked RecommenderService."""
    return AsyncMock(spec=RecommenderService)


@pytest.fixture
def client(mock_recommender_service: AsyncMock) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_recommender_service] = lambda: mock_recommender_service

    # Mock auth dependency
    # We can default to successful auth for most tests
    # If a test needs to fail auth, it can override this override or mock differently.
    async def mock_auth() -> dict[str, Any]:
        return {'pid': str(uuid.uuid4()), 'sid': str(uuid.uuid4())}

    app.dependency_overrides[validate_study_participant] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_recommendations_success(client: TestClient, mock_recommender_service: AsyncMock) -> None:
    """Test successful recommendation retrieval."""
    expected_response = EnrichedResponseWrapper(items=[], response_type='standard', total_count=0, rec_type='standard')
    mock_recommender_service.get_recommendations_for_study_participant.return_value = expected_response

    payload = {'context_tag': 'test'}
    response = client.post('/recommendations/', json=payload)

    assert response.status_code == 200
    assert response.json() == expected_response.model_dump(mode='json')
    mock_recommender_service.get_recommendations_for_study_participant.assert_called_once()


@pytest.mark.asyncio
async def test_get_recommendations_missing_context(client: TestClient, mock_recommender_service: AsyncMock) -> None:
    """Test failure when context data is missing."""
    response = client.post('/recommendations/', json=None)

    # The router explicitly raises 400 if context_data is None
    # FastAPI Body(default=None) allows it to be None, but router checks it.
    assert response.status_code == 400
    assert response.json()['detail'] == 'Missing context data.'
    mock_recommender_service.get_recommendations_for_study_participant.assert_not_called()


@pytest.mark.asyncio
async def test_get_recommendations_service_error(client: TestClient, mock_recommender_service: AsyncMock) -> None:
    """Test handling of underlying service errors."""
    mock_recommender_service.get_recommendations_for_study_participant.side_effect = ValueError('Service Error')

    payload = {'context_tag': 'test'}
    # FastAPI default exception handler for unhandled exceptions is 500
    with pytest.raises(ValueError):
        # We catch it here because TestClient propagates exceptions unless configured not to
        # By default starlette TestClient raises exceptions.
        client.post('/recommendations/', json=payload)

    mock_recommender_service.get_recommendations_for_study_participant.assert_called_once()
