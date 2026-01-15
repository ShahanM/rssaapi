"""Tests for the EnrollmentService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from rssa_storage.rssadb.models.study_components import StudyCondition
from rssa_storage.rssadb.models.study_participants import StudyParticipant, StudyParticipantType

from rssa_api.data.services.dependencies import EnrollmentService

# ---------------------------------------------------------
# Fixtures: Setup the Mocks once for all tests
# ---------------------------------------------------------


@pytest.fixture
def mock_participant_repo():
    # AsyncMock is required for 'await repo.create()'
    return AsyncMock()


@pytest.fixture
def mock_condition_repo():
    # AsyncMock is required for 'await repo.get_all_by_fields()'
    return AsyncMock()


@pytest.fixture
def mock_participant_type_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_participant_repo, mock_participant_type_repo, mock_condition_repo):
    """Initialize the service with the MOCKED repositories.

    No real database connection is created!
    """
    return EnrollmentService(
        participant_repo=mock_participant_repo,
        participant_type_repo=mock_participant_type_repo,
        study_condition_repo=mock_condition_repo,
    )


# ---------------------------------------------------------
# Test Cases
# ---------------------------------------------------------


@pytest.mark.asyncio
async def test_enroll_participant_success(
    service: EnrollmentService,
    mock_participant_repo: AsyncMock,
    mock_participant_type_repo: AsyncMock,
    mock_condition_repo: AsyncMock,
) -> None:
    """Scenario: Conditions exist, enrollment should succeed."""
    # 1. SETUP
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Create fake condition objects that the repo "finds"
    cond_a = MagicMock(spec=StudyCondition)
    cond_a.id = uuid.uuid4()
    cond_b = MagicMock(spec=StudyCondition)
    cond_b.id = uuid.uuid4()

    # Tell the mock repo: "When find_many is called, return this list"
    mock_condition_repo.find_many.return_value = [cond_a, cond_b]

    # Tell the mock participant type repo: "When find_one is called, return this list"
    mock_participant_type_repo.find_one.return_value = MagicMock(spec=StudyParticipantType)

    # Tell the mock participant repo to just return whatever it is given (simulating create)
    # And set an ID
    def create_side_effect(x):
        x.id = uuid.uuid4()
        return x

    mock_participant_repo.create.side_effect = create_side_effect

    from rssa_api.data.schemas.participant_schemas import StudyParticipantCreate

    new_participant = StudyParticipantCreate(
        participant_type_key='test',
        external_id='test_external_id',
        study_id=study_id,
        current_step_id=uuid.uuid4(),
        current_page_id=None,
    )

    # 2. EXECUTE
    result = await service.enroll_participant(study_id, new_participant)

    # 3. ASSERT

    # Verify we got a participant back
    assert isinstance(result, StudyParticipant)
    assert result.id is not None
    assert result.study_id == study_id

    # Verify logic: The condition_id must be one of the two we provided
    assert result.study_condition_id in [cond_a.id, cond_b.id]

    # Verify generic interactions
    mock_condition_repo.find_many.assert_called_once()
    mock_participant_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_enroll_participant_fails_no_conditions(
    service: EnrollmentService, mock_condition_repo: AsyncMock, mock_participant_repo: AsyncMock
) -> None:
    """Scenario: No active conditions found for study. Should raise 400."""
    # 1. SETUP
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Repo returns empty list
    mock_condition_repo.find_many.return_value = []

    from rssa_api.data.schemas.participant_schemas import StudyParticipantCreate

    new_participant = StudyParticipantCreate(
        participant_type_key='test',
        external_id='test_external_id',
        study_id=study_id,
        current_step_id=uuid.uuid4(),
    )

    # 2. EXECUTE & ASSERT
    with pytest.raises(ValueError) as exc_info:
        await service.enroll_participant(study_id, new_participant)

    assert 'No study conditions found' in str(exc_info.value)

    # Verify we NEVER tried to create a participant
    mock_participant_repo.create.assert_not_called()
