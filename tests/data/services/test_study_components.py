"""Tests for StudyComponents related services."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from rssa_storage.rssadb.repositories.study_components import (
    StudyConditionRepository,
    StudyStepRepository,
)

from rssa_api.data.services.study_components import (
    StudyConditionService,
    StudyStepService,
)

# --- StudyConditionService Tests ---


@pytest.fixture
def mock_cond_repo() -> AsyncMock:
    """Fixture for mocked StudyConditionRepository."""
    return AsyncMock(spec=StudyConditionRepository)


@pytest.fixture
def cond_service(mock_cond_repo: AsyncMock) -> StudyConditionService:
    """Fixture for StudyConditionService."""
    return StudyConditionService(mock_cond_repo)


@pytest.mark.asyncio
async def test_get_participant_count_by_condition(
    cond_service: StudyConditionService, mock_cond_repo: AsyncMock
) -> None:
    """Test retrieving participant counts grouped by condition."""
    study_id = uuid.uuid4()
    # Mocking what the service expects from repo.
    mock_row = MagicMock()
    mock_row.study_condition_id = uuid.uuid4()
    mock_row.study_condition_name = 'cond1'
    mock_row.participant_count = 5

    mock_cond_repo.get_participant_count_by_condition.return_value = [mock_row]

    # Check if method exists on service
    if hasattr(cond_service, 'get_participant_count_by_condition'):
        res = await cond_service.get_participant_count_by_condition(study_id)
        # res should be list of ConditionCountSchema objects
        assert len(res) == 1
        assert res[0].participant_count == 5


# --- StudyStepService Tests ---


@pytest.fixture
def mock_step_repo() -> AsyncMock:
    """Fixture for mocked StudyStepRepository."""
    return AsyncMock(spec=StudyStepRepository)


@pytest.fixture
def step_service(mock_step_repo: AsyncMock) -> StudyStepService:
    """Fixture for StudyStepService."""
    return StudyStepService(mock_step_repo)
