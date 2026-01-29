"""Tests for the participants router."""

import uuid
from collections.abc import Generator
from typing import Any, get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.params import Depends as FastAPI_Depends
from fastapi.testclient import TestClient

from rssa_api.apps.study.routers.studies.participant import router
from rssa_api.auth.authorization import validate_api_key, validate_study_participant
from rssa_api.data.services.dependencies import StudyParticipantServiceDep
from rssa_api.data.services.study_components import StudyParticipantService


def get_dependency_key(annotated_dep: Any) -> Any:  # noqa: ANN401
    """Extracts the dependency function from an Annotated dependency."""
    for item in get_args(annotated_dep):
        if isinstance(item, FastAPI_Depends):
            return item.dependency
    raise ValueError(f'Could not find Depends in {annotated_dep}')


@pytest.fixture
def mock_participant_service() -> AsyncMock:
    """Fixture for mocked StudyParticipantService."""
    return AsyncMock(spec=StudyParticipantService)


@pytest.fixture
def client(
    mock_participant_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_dependency_key(StudyParticipantServiceDep)] = lambda: mock_participant_service

    # Mock Auth
    study_id = uuid.UUID('7a878158-2eff-476f-919d-5778667ce68d')

    async def mock_api_key_auth() -> uuid.UUID:
        return study_id

    app.dependency_overrides[validate_api_key] = mock_api_key_auth

    async def mock_participant_auth() -> dict[str, uuid.UUID]:
        return {'pid': uuid.uuid4(), 'sid': uuid.uuid4()}

    app.dependency_overrides[validate_study_participant] = mock_participant_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_current_participant_success(client: TestClient, mock_participant_service: AsyncMock) -> None:
    """Test retrieving current participant successfully."""
    mock_participant = MagicMock()
    mock_participant.id = uuid.uuid4()
    mock_participant.study_id = uuid.uuid4()
    # Required by StudyParticipantReadWithCondition
    mock_participant.current_step_id = uuid.uuid4()
    mock_participant.current_page_id = None
    mock_participant.study_condition_id = uuid.uuid4()
    mock_participant.current_status = 'active'
    mock_participant.external_id = 'ext_id'
    mock_participant.created_at = '2023-01-01T00:00:00Z'
    mock_participant.updated_at = '2023-01-01T00:00:00Z'
    mock_participant.study_participant_type_id = uuid.uuid4()

    # Use simple objects instead of MagicMock for nested models to avoid auto-mocking
    class MockObj:
        def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401
            for k, v in kwargs.items():
                setattr(self, k, v)

    mock_condition = MockObj(
        id=uuid.uuid4(),
        name='Condition',
        study_id=mock_participant.study_id,
        recommendation_count=10,
        enabled=True,
        short_code='SC',
        description='Desc',
        recommender_key=None,
        created_by_id=None,
    )

    mock_type = MockObj(
        id=uuid.uuid4(),
        key='mturk',
        type='mturk',  # Verification alias
    )

    # We can keep mock_participant as MagicMock but set nested to real objs
    mock_participant.study_condition = mock_condition
    # Schema validation_alias='study_participant_type' means it looks for this attr
    mock_participant.study_participant_type = mock_type
    mock_participant.participant_type = mock_type

    mock_participant_service.get_participant_with_condition.return_value = mock_participant

    response = client.get('/participants/me')

    assert response.status_code == 200, response.text
    data = response.json()
    assert data['external_id'] == 'ext_id'


@pytest.mark.asyncio
async def test_get_current_participant_not_found(client: TestClient, mock_participant_service: AsyncMock) -> None:
    """Test retrieving participant when not found."""
    mock_participant_service.get_participant_with_condition.return_value = None

    response = client.get('/participants/me')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Participant not found.'


@pytest.mark.asyncio
async def test_create_demographics_success(client: TestClient, mock_participant_service: AsyncMock) -> None:
    """Test creating demographics successfully."""
    payload = {
        'age_range': '18-24',
        'gender': 'Female',
        'race': ['Asian'],
        'education': 'Bachelor',
        'country': 'US',
        'state_region': 'CA',
        'gender_other': None,
        'race_other': None,
    }

    # Mock return value should match DemographicsCreate/Read (from_attributes=True)
    mock_demo = MagicMock()
    mock_demo.age_range = '18-24'
    mock_demo.gender = 'Female'
    mock_demo.race = ['Asian']
    mock_demo.education = 'Bachelor'
    mock_demo.country = 'US'
    mock_demo.state_region = 'CA'
    mock_demo.gender_other = None
    mock_demo.race_other = None

    mock_participant_service.create_demographic_info.return_value = mock_demo

    response = client.post('/participants/demographics', json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data['age_range'] == '18-24'


@pytest.mark.asyncio
async def test_create_demographics_failure(client: TestClient, mock_participant_service: AsyncMock) -> None:
    """Test failure in creating demographics."""
    payload = {
        'age_range': '18-24',
        'gender': 'Female',
        'race': ['Asian'],
        'education': 'Bachelor',
        'country': 'US',
        'state_region': 'CA',
        'gender_other': None,
        'race_other': None,
    }

    mock_participant_service.create_demographic_info.return_value = None

    response = client.post('/participants/demographics', json=payload)

    assert response.status_code == 500
    assert response.json()['detail'] == 'Something went wrong, could not record demographic data.'
