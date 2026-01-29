"""Tests for the studies router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.study_components.studies import router
from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import (
    ApiKeyServiceDep,
    StudyConditionServiceDep,
    StudyParticipantServiceDep,
    StudyServiceDep,
    StudyStepServiceDep,
)


# Helper to override dependency
def override_dep(app, dep, mock) -> None:
    """Helper to override dependency."""
    from typing import get_args

    from fastapi.params import Depends as FastAPI_Depends

    dep_callable = None
    for item in get_args(dep):
        if isinstance(item, FastAPI_Depends):
            dep_callable = item.dependency
            break

    if dep_callable:
        app.dependency_overrides[dep_callable] = lambda: mock
    else:
        app.dependency_overrides[dep] = lambda: mock


@pytest.fixture
def mock_study_service() -> AsyncMock:
    """Fixture for a mocked StudyService."""
    return AsyncMock()


@pytest.fixture
def mock_study_participant_service() -> AsyncMock:
    """Fixture for a mocked StudyParticipantService."""
    return AsyncMock()


@pytest.fixture
def mock_condition_service() -> AsyncMock:
    """Fixture for a mocked StudyConditionService."""
    return AsyncMock()


@pytest.fixture
def mock_step_service() -> AsyncMock:
    """Fixture for a mocked StudyStepService."""
    return AsyncMock()


@pytest.fixture
def mock_apikey_service() -> AsyncMock:
    """Fixture for a mocked ApiKeyService."""
    return AsyncMock()


@pytest.fixture
def client(
    mock_study_service: AsyncMock,
    mock_study_participant_service: AsyncMock,
    mock_condition_service: AsyncMock,
    mock_step_service: AsyncMock,
    mock_apikey_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    override_dep(app, StudyServiceDep, mock_study_service)
    override_dep(app, StudyParticipantServiceDep, mock_study_participant_service)
    override_dep(app, StudyConditionServiceDep, mock_condition_service)
    override_dep(app, StudyStepServiceDep, mock_step_service)
    override_dep(app, ApiKeyServiceDep, mock_apikey_service)

    # Mock Auth0 user
    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(
            sub='auth0|user123', email='user@test.com', permissions=['admin:all', 'read:studies', 'create:studies']
        )

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    # Mock Current User (DB User)
    mock_user = MagicMock()
    mock_user.id = str(uuid.uuid4())
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_studies(client: TestClient, mock_study_service: AsyncMock) -> None:
    """Test retrieving a list of studies."""
    mock_study = MagicMock()
    mock_study.id = uuid.uuid4()
    mock_study.name = 'Test Study'
    mock_study.description = 'Desc'
    mock_study.status = 'draft'
    mock_study.created_at = '2023-01-01'
    mock_study.updated_at = '2023-01-01'
    mock_study.owner_id = uuid.uuid4()

    mock_study_service.count.return_value = 1
    mock_study_service.get_paged_list.return_value = [mock_study]
    mock_study_service.get_paged_for_owner.return_value = [mock_study]

    response = client.get('/studies/')

    assert response.status_code == 200, response.text
    data = response.json()
    assert data['page_count'] == 1
    assert len(data['rows']) == 1
    assert data['rows'][0]['name'] == 'Test Study'


@pytest.mark.asyncio
async def test_get_study_detail(
    client: TestClient, mock_study_service: AsyncMock, mock_condition_service: AsyncMock
) -> None:
    """Test retrieving study details."""
    study_id = uuid.uuid4()

    # Use a real dict for model_dump return to be safe
    study_data = {
        'id': study_id,
        'name': 'Detailed Study',
        'status': 'active',
        'created_at': '2023-01-01',
        'updated_at': '2023-01-01',
        'description': '',
        'owner_id': uuid.uuid4(),
        'instructions': 'Instructions',
        'consent': 'Consent',
        'completion': 'Completion',
        'meta_data': {},
        'redirect_url': '',
        'redirect_secret': '',
        'is_public': True,
        'logo_url': '',
        # Add other fields if StudyAudit requires them
    }

    mock_study_obj = MagicMock()
    mock_study_obj.model_dump.return_value = study_data

    mock_study_service.get_detailed.return_value = mock_study_obj

    mock_row = MagicMock()
    mock_row.participant_count = 10
    mock_row.study_condition_name = 'Control'
    mock_row.study_condition_id = uuid.uuid4()

    mock_condition_service.get_participant_count_by_condition.return_value = [mock_row]

    response = client.get(f'/studies/{study_id}')

    assert response.status_code == 200, response.text
    data = response.json()
    assert data['name'] == 'Detailed Study'
    assert data['total_participants'] == 10


@pytest.mark.asyncio
async def test_create_study(client: TestClient, mock_study_service: AsyncMock) -> None:
    """Test creating a new study."""
    payload = {'name': 'New Study', 'description': 'New Description', 'status': 'draft'}

    mock_study = MagicMock()
    mock_study.id = uuid.uuid4()
    mock_study.name = 'New Study'
    mock_study.description = 'New Description'
    mock_study.status = 'draft'
    mock_study.created_at = '2023-01-01'
    mock_study.updated_at = '2023-01-01'
    mock_study.owner_id = uuid.uuid4()

    mock_study_service.create_for_owner.return_value = mock_study

    response = client.post('/studies/', json=payload)

    assert response.status_code == 201
    assert response.json()['name'] == 'New Study'


@pytest.mark.asyncio
async def test_get_study_steps(client: TestClient, mock_step_service: AsyncMock) -> None:
    """Test retrieving study steps."""
    study_id = uuid.uuid4()
    mock_step = MagicMock()
    mock_step.id = uuid.uuid4()
    mock_step.order_position = 1
    mock_step.name = 'Step 1'

    mock_step_service.get_items_for_owner_as_ordered_list.return_value = [mock_step]

    response = client.get(f'/studies/{study_id}/steps')
    assert response.status_code == 200
    assert len(response.json()) == 1
