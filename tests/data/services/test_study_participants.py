"""Tests for StudyParticipant related services."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rssa_storage.rssadb.repositories.study_components import StudyConditionRepository
from rssa_storage.rssadb.repositories.study_participants import (
    ParticipantDemographicRepository,
    ParticipantRecommendationContextRepository,
    StudyParticipantRepository,
    StudyParticipantTypeRepository,
)

from rssa_api.data.services.study_components import StudyParticipantService
from rssa_api.data.services.study_participants import (
    EnrollmentService,
    FeedbackService,
)

# --- EnrollmentService Tests ---


@pytest.fixture
def mock_enroll_repos() -> dict[str, AsyncMock]:
    """Fixture for mocked repositories used by EnrollmentService."""
    return {
        'participant': AsyncMock(spec=StudyParticipantRepository),
        'type': AsyncMock(spec=StudyParticipantTypeRepository),
        'condition': AsyncMock(spec=StudyConditionRepository),
    }


@pytest.fixture
def enrollment_service(mock_enroll_repos: dict[str, AsyncMock]) -> EnrollmentService:
    """Fixture for EnrollmentService."""
    return EnrollmentService(
        participant_repo=mock_enroll_repos['participant'],
        participant_type_repo=mock_enroll_repos['type'],
        study_condition_repo=mock_enroll_repos['condition'],
    )


@pytest.mark.asyncio
async def test_enroll_participant_success(
    enrollment_service: EnrollmentService, mock_enroll_repos: dict[str, AsyncMock]
) -> None:
    """Test successful enrollment of a new participant."""
    study_id = uuid.uuid4()
    new_p_data = MagicMock()
    new_p_data.prolific_id = 'pid'

    # Setup mocks
    mock_enroll_repos['participant'].find_one.return_value = None  # New participant
    mock_enroll_repos['type'].find_one.return_value = MagicMock(id=uuid.uuid4())

    condition = MagicMock()
    condition.id = uuid.uuid4()
    mock_enroll_repos['condition'].find_many.return_value = [condition]

    mock_enroll_repos['participant'].create.return_value = MagicMock(id=uuid.uuid4())

    result = await enrollment_service.enroll_participant(study_id, new_p_data)

    mock_enroll_repos['participant'].create.assert_called_once()
    assert result is not None


# --- StudyParticipantService Tests ---


@pytest.fixture
def mock_sp_repos() -> dict[str, AsyncMock]:
    """Fixture for mocked repositories used by StudyParticipantService."""
    return {
        'participant': AsyncMock(spec=StudyParticipantRepository),
        'demo': AsyncMock(spec=ParticipantDemographicRepository),
        'context': AsyncMock(spec=ParticipantRecommendationContextRepository),
    }


@pytest.fixture
def sp_service(mock_sp_repos: dict[str, AsyncMock]) -> StudyParticipantService:
    """Fixture for StudyParticipantService."""
    return StudyParticipantService(
        participant_repo=mock_sp_repos['participant'],
        demographics_repo=mock_sp_repos['demo'],
        recommendation_context_repo=mock_sp_repos['context'],
    )


@pytest.mark.asyncio
async def test_get_participant_with_condition(
    sp_service: StudyParticipantService, mock_sp_repos: dict[str, AsyncMock]
) -> None:
    """Test retrieving a participant along with their assigned condition."""
    pid = uuid.uuid4()
    sp_service.get = AsyncMock()  # Inherited method

    mock_sp_repos['participant'].find_one.return_value = 'participant'

    res = await sp_service.get_participant_with_condition(pid)
    assert res == 'participant'
    mock_sp_repos['participant'].find_one.assert_called_once()
    # verify load options
    opts = mock_sp_repos['participant'].find_one.call_args[0][0]
    # Expect load options for condition
    assert opts.load_options is not None


@pytest.mark.asyncio
async def test_create_recommendation_context(
    sp_service: StudyParticipantService, mock_sp_repos: dict[str, AsyncMock]
) -> None:
    """Test creating a recommendation context for a participant."""
    study_id = uuid.uuid4()
    pid = uuid.uuid4()

    # Context data must be a Schema object or Mock with correct types
    context_data = MagicMock()
    context_data.step_id = uuid.uuid4()
    context_data.step_page_id = uuid.uuid4()
    context_data.context_tag = 'tag'
    context_data.recommendations_json = MagicMock()
    context_data.recommendations_json.model_dump.return_value = {}

    # Mock create to set ID on instance (simulating DB commit)
    def set_id(instance) -> Any:
        instance.id = uuid.uuid4()
        return instance

    mock_sp_repos['context'].create.side_effect = set_id

    # Use patch to ensure serialization works if needed, or trust service logic
    res = await sp_service.create_recommendation_context(study_id, pid, context_data)

    assert res is not None
    mock_sp_repos['context'].create.assert_called_once()


@pytest.mark.asyncio
async def test_create_demographic_info(
    sp_service: StudyParticipantService, mock_sp_repos: dict[str, AsyncMock]
) -> None:
    """Test storing demographic information for a participant."""
    pid = uuid.uuid4()
    # Mock DemographicsCreate schema
    demo_data = MagicMock()
    # Attributes required by service
    demo_data.age_range = '18-24'
    demo_data.gender = 'Non-binary'
    demo_data.gender_other = None
    demo_data.race = ['Asian', 'White']
    demo_data.race_other = None
    demo_data.education = 'Bachelor'
    demo_data.country = 'USA'
    demo_data.state_region = 'CA'

    mock_sp_repos['demo'].create.return_value = 'created_demo'

    # Patch DemographicsCreate.model_validate to return something
    with patch('rssa_api.data.services.study_components.DemographicsCreate') as MockSchema:
        MockSchema.model_validate.return_value = 'validated_demo'

        res = await sp_service.create_demographic_info(pid, demo_data)

        assert res == 'validated_demo'
        mock_sp_repos['demo'].create.assert_called_once()
        # Verify call args if strict correctness needed (e.g. race join)
        call_arg = mock_sp_repos['demo'].create.call_args[0][0]
        assert call_arg.race == 'Asian;White'


# --- FeedbackService Tests ---


@pytest.fixture
def mock_feedback_repo() -> AsyncMock:
    """Fixture for mocked FeedbackRepository."""
    return AsyncMock()


@pytest.fixture
def feedback_service(mock_feedback_repo: AsyncMock) -> FeedbackService:
    """Fixture for FeedbackService."""
    # FeedbackService is in study_participants.py
    return FeedbackService(mock_feedback_repo)


@pytest.mark.asyncio
async def test_create_feedback(feedback_service: FeedbackService, mock_feedback_repo: AsyncMock) -> None:
    """Test creating user feedback."""
    study_id = uuid.uuid4()
    pid = uuid.uuid4()

    feedback_data = MagicMock()
    feedback_data.study_step_id = uuid.uuid4()
    feedback_data.study_step_page_id = uuid.uuid4()
    feedback_data.context_tag = 'tag'
    feedback_data.feedback_text = 'Good'
    feedback_data.feedback_type = 'bug'
    feedback_data.feedback_category = 'ui'

    mock_feedback_repo.create.return_value = 'fb'

    res = await feedback_service.create_feedback(study_id, pid, feedback_data)

    assert res == 'fb'
    mock_feedback_repo.create.assert_called_once()
