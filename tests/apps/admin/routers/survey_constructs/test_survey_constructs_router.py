"""Tests for the survey constructs router."""

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.survey_constructs.survey_constructs import router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.services.dependencies import SurveyConstructServiceDep, SurveyItemServiceDep


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
def mock_construct_service() -> AsyncMock:
    """Mock construct service."""
    return AsyncMock()


@pytest.fixture
def mock_item_service() -> AsyncMock:
    """Mock item service."""
    return AsyncMock()


@pytest.fixture
def client(
    mock_construct_service: AsyncMock,
    mock_item_service: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Fixture for a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    override_dep(app, SurveyConstructServiceDep, mock_construct_service)
    override_dep(app, SurveyItemServiceDep, mock_item_service)

    # Mock Auth0 user
    async def mock_auth() -> Auth0UserSchema:
        return Auth0UserSchema(
            sub='auth0|user123',
            email='user@test.com',
            permissions=[
                'admin:all',
                'read:constructs',
                'create:constructs',
                'update:constructs',
                'delete:constructs',
                'create:items',
            ],
        )

    app.dependency_overrides[get_auth0_authenticated_user] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_survey_constructs(client: TestClient, mock_construct_service: AsyncMock) -> None:
    """Test retrieving a list of survey constructs."""
    mock_construct = MagicMock()
    mock_construct.name = 'Test Construct'
    mock_construct.description = 'Test Description'
    mock_construct.id = uuid.uuid4()
    mock_construct.created_at = '2023-01-01'
    mock_construct.updated_at = '2023-01-01'

    # Mock return values
    mock_construct_service.count.return_value = 1
    mock_construct_service.get_paged_list.return_value = [mock_construct]

    response = client.get('/constructs/')

    assert response.status_code == 200
    data = response.json()
    assert data['page_count'] == 1
    assert len(data['rows']) == 1
    assert data['rows'][0]['name'] == 'Test Construct'


def test_get_construct_detail(client: TestClient, mock_construct_service: AsyncMock) -> None:
    """Test retrieving details of a specific survey construct."""
    construct_id = uuid.uuid4()

    mock_construct = MagicMock()
    mock_construct.id = construct_id
    mock_construct.name = 'Detailed Construct'
    mock_construct.description = 'Detailed Description'
    mock_construct.created_at = '2023-01-01'
    mock_construct.updated_at = '2023-01-01'

    mock_construct_service.get_detailed.return_value = mock_construct

    response = client.get(f'/constructs/{construct_id}')

    assert response.status_code == 200
    assert response.json()['name'] == 'Detailed Construct'


def test_create_survey_construct(client: TestClient, mock_construct_service: AsyncMock) -> None:
    """Test creating a new survey construct."""
    payload = {'name': 'New Construct', 'description': 'New Description'}

    response = client.post('/constructs/', json=payload)

    assert response.status_code == 201
    assert response.json() == {'message': 'Survey construct created.'}
    mock_construct_service.create.assert_called_once()


def test_update_survey_construct(client: TestClient, mock_construct_service: AsyncMock) -> None:
    """Test updating a survey construct."""
    construct_id = uuid.uuid4()
    payload = {'name': 'Updated Name'}

    response = client.patch(f'/constructs/{construct_id}', json=payload)

    assert response.status_code == 204
    mock_construct_service.update.assert_called_once_with(construct_id, payload)


def test_delete_construct(client: TestClient, mock_construct_service: AsyncMock) -> None:
    """Test deleting a survey construct."""
    construct_id = uuid.uuid4()

    response = client.delete(f'/constructs/{construct_id}')

    assert response.status_code == 204
    mock_construct_service.delete.assert_called_once_with(construct_id)


def test_create_construct_item(client: TestClient, mock_item_service: AsyncMock) -> None:
    """Test creating an item for a survey construct."""
    construct_id = uuid.uuid4()
    payload = {'text': 'New Item Text', 'survey_construct_id': str(construct_id)}

    response = client.post(f'/constructs/{construct_id}/items', json=payload)

    assert response.status_code == 201
    assert response.json() == {'message': 'Construct item created.'}
    mock_item_service.create_for_owner.assert_called_once()
