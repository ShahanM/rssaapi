"""Tests for local_users router."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rssa_api.apps.admin.routers.local_users import router as local_users_router
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema, UserSchema
from rssa_api.data.services.dependencies import UserServiceDep


@pytest.fixture
def mock_user_service() -> AsyncMock:
    """Mock user service."""
    return AsyncMock()


@pytest.fixture
def app(mock_user_service) -> FastAPI:
    """Create a FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(local_users_router)

    from typing import get_args

    from fastapi.params import Depends as FastAPI_Depends

    def override_dep(dep_type, mock_instance) -> None:
        dep_callable = None
        for item in get_args(dep_type):
            if isinstance(item, FastAPI_Depends):
                dep_callable = item.dependency
                break
        if dep_callable:
            app.dependency_overrides[dep_callable] = lambda: mock_instance
        else:
            app.dependency_overrides[dep_type] = lambda: mock_instance

    override_dep(UserServiceDep, mock_user_service)

    return app


@pytest.mark.asyncio
async def test_get_local_users_success(app: FastAPI, mock_user_service: AsyncMock) -> None:
    """Test getting local users list with admin:all permission."""
    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|admin', email='admin@test.com', permissions=['admin:all']
    )

    mock_user_service.count.return_value = 1
    mock_user_service.get_paged_list.return_value = [
        UserSchema(
            id=uuid.uuid4(),
            auth0_sub='auth0|test',
            email='test@example.com',
            desc='Test User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    ]

    with TestClient(app) as client:
        response = client.get('/local-users/')

    assert response.status_code == 200
    data = response.json()
    assert data['page_count'] == 1
    assert len(data['rows']) == 1
    assert data['rows'][0]['email'] == 'test@example.com'
    assert 'created_at' in data['rows'][0]
    assert 'updated_at' in data['rows'][0]


@pytest.mark.asyncio
async def test_get_local_users_forbidden(app: FastAPI, mock_user_service: AsyncMock) -> None:
    """Test getting local users without admin:all permission."""
    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|user', email='user@test.com', permissions=['read:some_other_thing']
    )

    with TestClient(app) as client:
        response = client.get('/local-users/')

    assert response.status_code == 403
    assert 'User lacks required permissions' in response.text


@pytest.mark.asyncio
async def test_get_user_detail_success(app: FastAPI, mock_user_service: AsyncMock) -> None:
    """Test getting user detail."""
    user_id = uuid.uuid4()
    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|admin', email='admin@test.com', permissions=['admin:all']
    )

    mock_user_service.get_detailed.return_value = UserSchema(
        id=user_id,
        auth0_sub='auth0|test',
        email='test@example.com',
        desc='Test User',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    with TestClient(app) as client:
        response = client.get(f'/local-users/{user_id}')

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == str(user_id)
    assert data['email'] == 'test@example.com'
    assert 'created_at' in data
    assert 'updated_at' in data


@pytest.mark.asyncio
async def test_get_user_detail_not_found(app: FastAPI, mock_user_service: AsyncMock) -> None:
    """Test getting user detail not found."""
    user_id = uuid.uuid4()
    app.dependency_overrides[get_auth0_authenticated_user] = lambda: Auth0UserSchema(
        sub='auth0|admin', email='admin@test.com', permissions=['admin:all']
    )

    mock_user_service.get_detailed.return_value = None

    with TestClient(app) as client:
        response = client.get(f'/local-users/{user_id}')

    assert response.status_code == 404
