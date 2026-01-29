"""Tests for the survey scales router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.survey_constructs.survey_scales import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import SurveyScaleLevelServiceDep, SurveyScaleServiceDep


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
def mock_scale_service() -> AsyncMock:
    """Mock scale service."""
    return AsyncMock()


@pytest.fixture
def mock_level_service() -> AsyncMock:
    """Mock level service."""
    return AsyncMock()


@pytest.fixture
def client(
    mock_scale_service: AsyncMock,
    mock_level_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    override_dep(app, SurveyScaleServiceDep, mock_scale_service)
    override_dep(app, SurveyScaleLevelServiceDep, mock_level_service)

    # Mock Auth0 user
    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(
            sub='auth0|user123',
            email='user@test.com',
            permissions=[
                'admin:all',
                'read:scales',
                'create:scales',
                'update:scales',
                'delete:scales',
                'create:levels',
            ],
        )

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_construct_scales(client: TestClient, mock_scale_service: AsyncMock) -> None:
    """Test retrieving a list of survey scales."""
    mock_scale = MagicMock()
    mock_scale.name = 'Test Scale'
    mock_scale.description = 'Test Description'
    mock_scale.id = uuid.uuid4()
    mock_scale.created_at = '2023-01-01'
    mock_scale.updated_at = '2023-01-01'

    mock_scale_service.count.return_value = 1
    mock_scale_service.get_paged_list.return_value = [mock_scale]

    response = client.get('/scales/')

    assert response.status_code == 200
    data = response.json()
    assert data['page_count'] == 1
    assert data['rows'][0]['name'] == 'Test Scale'


def test_create_construct_scale(client: TestClient, mock_scale_service: AsyncMock) -> None:
    """Test creating a new survey scale."""
    payload = {'name': 'New Scale', 'description': 'Scale Description'}

    response = client.post('/scales/', json=payload)

    assert response.status_code == 201
    assert response.json() == {'message': 'Construct Scale created'}
    mock_scale_service.create.assert_called_once()


def test_get_construct_scale_detail(client: TestClient, mock_scale_service: AsyncMock) -> None:
    """Test retrieving details of a specific survey scale."""
    scale_id = uuid.uuid4()

    mock_scale = MagicMock()
    mock_scale.id = scale_id
    mock_scale.name = 'Detailed Scale'
    mock_scale.description = 'Detailed Description'
    mock_scale.created_at = '2023-01-01'
    mock_scale.updated_at = '2023-01-01'

    mock_scale_service.get_detailed.return_value = mock_scale

    response = client.get(f'/scales/{scale_id}')

    assert response.status_code == 200
    assert response.json()['name'] == 'Detailed Scale'


def test_update_survey_scale(client: TestClient, mock_scale_service: AsyncMock) -> None:
    """Test updating a survey scale."""
    scale_id = uuid.uuid4()
    payload = {'name': 'Updated Scale Name'}

    response = client.patch(f'/scales/{scale_id}', json=payload)

    assert response.status_code == 204
    mock_scale_service.update.assert_called_once_with(scale_id, payload)


def test_get_scale_levels(client: TestClient, mock_level_service: AsyncMock) -> None:
    """Test retrieving levels for a survey scale."""
    scale_id = uuid.uuid4()

    mock_level = MagicMock()
    mock_level.id = uuid.uuid4()
    mock_level.survey_scale_id = scale_id
    mock_level.value = 1
    mock_level.label = 'Level 1'
    mock_level.order_position = 1
    mock_level.created_at = '2023-01-01'
    mock_level.updated_at = '2023-01-01'

    mock_level_service.get_items_for_owner_as_ordered_list.return_value = [mock_level]

    response = client.get(f'/scales/{scale_id}/levels')

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['label'] == 'Level 1'


def test_create_scale_level(client: TestClient, mock_level_service: AsyncMock) -> None:
    """Test creating a level for a survey scale."""
    scale_id = uuid.uuid4()
    payload = {'survey_scale_id': str(scale_id), 'value': 2, 'label': 'Level 2'}

    mock_level = MagicMock()
    mock_level.id = uuid.uuid4()
    mock_level.survey_scale_id = scale_id
    mock_level.value = 2
    mock_level.label = 'Level 2'
    mock_level.order_position = 2
    mock_level.created_at = '2023-01-01'
    mock_level.updated_at = '2023-01-01'

    mock_level_service.create_for_owner.return_value = mock_level

    response = client.post(f'/scales/{scale_id}/levels', json=payload)

    assert response.status_code == 200
    assert response.json()['label'] == 'Level 2'
    mock_level_service.create_for_owner.assert_called_once()
