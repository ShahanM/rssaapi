"""Tests for the studies router."""

import datetime
import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.studies import router
from rssa_api.auth.authorization import authorize_api_key_for_study
from rssa_api.data.services.dependencies import (
    EnrollmentServiceDep,
    ParticipantStudySessionServiceDep,
    StudyConditionServiceDep,
    StudyParticipantMovieSessionServiceDep,
    StudyParticipantServiceDep,
    StudyStepServiceDep,
)
from rssa_api.data.services.study_components import (
    StudyConditionService,
    StudyParticipantService,
    StudyStepService,
)
from rssa_api.data.services.study_participants import (
    EnrollmentService,
    ParticipantStudySessionService,
    StudyParticipantMovieSessionService,
)


# Mock Services
@pytest.fixture
def mock_step_service() -> AsyncMock:
    """Fixture for mocked StudyStepService."""
    return AsyncMock(spec=StudyStepService)


@pytest.fixture
def mock_condition_service() -> AsyncMock:
    """Fixture for mocked StudyConditionService."""
    return AsyncMock(spec=StudyConditionService)


@pytest.fixture
def mock_enrollment_service() -> AsyncMock:
    """Fixture for mocked EnrollmentService."""
    return AsyncMock(spec=EnrollmentService)


@pytest.fixture
def mock_session_service() -> AsyncMock:
    """Fixture for mocked ParticipantStudySessionService."""
    return AsyncMock(spec=ParticipantStudySessionService)


@pytest.fixture
def mock_movie_session_service() -> AsyncMock:
    """Fixture for mocked StudyParticipantMovieSessionService."""
    return AsyncMock(spec=StudyParticipantMovieSessionService)


@pytest.fixture
def mock_participant_service() -> AsyncMock:
    """Fixture for mocked StudyParticipantService."""
    return AsyncMock(spec=StudyParticipantService)


def get_dependency_key(annotated_dep: Any) -> Any:  # noqa: ANN401
    """Extracts the dependency function from an Annotated dependency."""
    # get_args returns (type, *metadata)
    # The metadata should contain the Depends object
    for item in get_args(annotated_dep):
        if isinstance(item, FastAPI_Depends):
            return item.dependency
    raise ValueError(f'Could not find Depends in {annotated_dep}')


@pytest.fixture
def client(
    mock_step_service: AsyncMock,
    mock_condition_service: AsyncMock,
    mock_enrollment_service: AsyncMock,
    mock_session_service: AsyncMock,
    mock_movie_session_service: AsyncMock,
    mock_participant_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_dependency_key(StudyStepServiceDep)] = lambda: mock_step_service
    app.dependency_overrides[get_dependency_key(StudyConditionServiceDep)] = lambda: mock_condition_service
    app.dependency_overrides[get_dependency_key(EnrollmentServiceDep)] = lambda: mock_enrollment_service
    app.dependency_overrides[get_dependency_key(ParticipantStudySessionServiceDep)] = lambda: mock_session_service
    app.dependency_overrides[get_dependency_key(StudyParticipantMovieSessionServiceDep)] = (
        lambda: mock_movie_session_service
    )
    app.dependency_overrides[get_dependency_key(StudyParticipantServiceDep)] = lambda: mock_participant_service

    # Mock Auth
    async def mock_auth() -> uuid.UUID:
        return uuid.uuid4()

    app.dependency_overrides[authorize_api_key_for_study] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_first_step_success(client: TestClient, mock_step_service: AsyncMock) -> None:
    """Test retrieving the first step successfully."""
    study_id = uuid.uuid4()

    mock_step = MagicMock()
    mock_step.id = uuid.uuid4()
    mock_step.path = '/first'
    mock_step.step_type = 'consent'
    mock_step.key = 'step_key'
    mock_step.study_id = study_id
    mock_step.title = 'Step Title'
    mock_step.instructions = 'Instructions'
    mock_step.name = 'Step Name'
    mock_step.description = 'Description'
    mock_step.survey_api_root = 'http://api.root'
    mock_step.root_page_info = {
        'data': {
            'id': uuid.uuid4(),
            'name': 'Page Name',
            'description': 'Page Description',
            'study_id': study_id,
            'study_step_id': mock_step.id,
            'study_step_page_contents': [],
            'order_position': 1,
        },
        'next_id': None,
        'next_path': None,
    }

    mock_step_service.get_first_with_navigation.return_value = {
        'current': mock_step,
        'next_id': uuid.uuid4(),
        'next_path': '/next',
    }

    response = client.get(f'/studies/{study_id}/steps/first')

    assert response.status_code == 200
    mock_step_service.get_first_with_navigation.assert_called_once()


@pytest.mark.asyncio
async def test_export_study_config(
    client: TestClient, mock_step_service: AsyncMock, mock_condition_service: AsyncMock
) -> None:
    """Test exporting study configuration."""
    study_id = uuid.uuid4()

    mock_step = MagicMock()
    mock_step.id = uuid.uuid4()
    mock_step.path = '/first'
    # Ensure step_type is one of the keys in STEP_TYPE_TO_COMPONENT
    mock_step.step_type = 'consent'

    mock_condition = MagicMock()
    mock_condition.id = uuid.uuid4()
    mock_condition.name = 'cond1'

    mock_step_service.get_items_for_owner_as_ordered_list.return_value = [mock_step]
    mock_condition_service.get_all_for_owner.return_value = [mock_condition]

    response = client.get(f'/studies/{study_id}/config')

    assert response.status_code == 200
    data = response.json()
    assert str(study_id) == data['study_id']
    assert len(data['steps']) == 1
    assert data['steps'][0]['component_type'] == 'ConsentStep'


@pytest.mark.asyncio
async def test_create_new_participant_fail_missing_step(client: TestClient, mock_step_service: AsyncMock) -> None:
    """Test enrollment failing when next step is missing."""
    study_id = uuid.uuid4()
    payload = {
        'prolific_id': 'pid',
        'current_step_id': str(uuid.uuid4()),
        'participant_type_key': 'participant',
        'external_id': 'ext_id',
    }

    mock_step_service.get_with_navigation.return_value = None

    response = client.post(f'/studies/{study_id}/new-participant', json=payload)

    assert response.status_code == 500
    assert response.json()['detail'] == 'Could not find next step, study is configuration fault.'


@pytest.mark.asyncio
async def test_resume_study_session_success(
    client: TestClient,
    mock_session_service: AsyncMock,
    mock_participant_service: AsyncMock,
) -> None:
    """Test resuming a study session."""
    study_id = uuid.uuid4()

    async def specific_auth() -> uuid.UUID:
        return study_id

    client.app.dependency_overrides[authorize_api_key_for_study] = specific_auth

    # Now setup session and participant
    payload = {'resume_code': 'CODE123'}

    mock_session = MagicMock()
    mock_session.id = uuid.uuid4()
    mock_session.study_participant_id = uuid.uuid4()
    mock_session.expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
    mock_session.is_active = True

    mock_session_service.get_session_by_resume_code.return_value = mock_session

    mock_participant = MagicMock()
    mock_participant.id = mock_session.study_participant_id
    mock_participant.study_id = study_id  # Must match
    mock_participant.current_step_id = uuid.uuid4()
    mock_participant.current_page_id = None

    mock_participant_service.get.return_value = mock_participant

    response = client.post(f'/studies/{study_id}/resume', json=payload)

    assert response.status_code == 200
    assert 'token' in response.json()
