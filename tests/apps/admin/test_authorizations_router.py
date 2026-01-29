"""Test the authorizations router."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status

from rssa_api.apps.admin.routers.study_components.authorizations import (
    delete_study_authorization,
    get_study_authorization,
)
from rssa_api.data.schemas.study_components import StudyAuthorizationRead


@pytest.fixture
def mock_service() -> AsyncMock:
    """Mock study authorization service."""
    return AsyncMock()


@pytest.fixture
def mock_user_schema() -> MagicMock:
    """Mock user schema."""
    return MagicMock()


@pytest.mark.asyncio
async def test_get_study_authorization_success(mock_service: AsyncMock, mock_user_schema: MagicMock) -> None:
    """Test getting a study authorization."""
    auth_id = uuid.uuid4()
    mock_auth = MagicMock()
    mock_auth.id = auth_id
    mock_auth.study_id = uuid.uuid4()
    mock_auth.user_id = uuid.uuid4()
    mock_auth.role = 'viewer'

    mock_service.get_one.return_value = mock_auth

    result = await get_study_authorization(auth_id, mock_service, mock_user_schema)

    assert isinstance(result, StudyAuthorizationRead)
    assert result.id == auth_id
    mock_service.get_one.assert_called_with(auth_id)


@pytest.mark.asyncio
async def test_delete_study_authorization_success(mock_service: AsyncMock, mock_user_schema: MagicMock) -> None:
    """Test deleting a study authorization."""
    auth_id = uuid.uuid4()
    mock_auth = MagicMock()
    mock_service.get_one.return_value = mock_auth

    await delete_study_authorization(auth_id, mock_service, mock_user_schema)

    mock_service.delete.assert_called_with(auth_id)


@pytest.mark.asyncio
async def test_delete_study_authorization_not_found(mock_service: AsyncMock, mock_user_schema: MagicMock) -> None:
    """Test deleting a study authorization that does not exist."""
    auth_id = uuid.uuid4()
    mock_service.get_one.return_value = None

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        await delete_study_authorization(auth_id, mock_service, mock_user_schema)

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
