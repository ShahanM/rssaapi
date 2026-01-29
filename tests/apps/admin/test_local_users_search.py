"""Tests for the users router."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from rssa_api.apps.admin.routers.users import search_local_users
from rssa_api.data.schemas import UserSchema


@pytest.fixture
def mock_user_service() -> AsyncMock:
    """Mock user service."""
    return AsyncMock()


@pytest.fixture
def mock_user_schema() -> MagicMock:
    """Mock user schema."""
    return MagicMock()


@pytest.mark.asyncio
async def test_search_local_users_success(mock_user_service: AsyncMock, mock_user_schema: MagicMock) -> None:
    """Test searching local users successfully."""
    mock_user = UserSchema(
        id=uuid.uuid4(),
        email='test@example.com',
        auth0_sub='auth0|123',
        is_active=True,
        created_at='2021-01-01T00:00:00',
    )

    # Mock return from service
    mock_user_service.search_users.return_value = [mock_user]

    result = await search_local_users(mock_user_service, mock_user_schema, q='test')

    assert len(result) == 1
    assert isinstance(result[0], UserSchema)
    # Note: UserSchema validation might fail if mock object attributes don't match exactly what Pydantic expects
    # In a real test we'd use proper objects, but for unit testing the router logic,
    # ensuring the service is called is the main thing.
    # However, since response_model is enforced, result will be validated models.
    mock_user_service.search_users.assert_called_with('test')


@pytest.mark.asyncio
async def test_search_local_users_empty_query(mock_user_service: AsyncMock, mock_user_schema: MagicMock) -> None:
    """Test that empty query returns empty list."""
    result = await search_local_users(mock_user_service, mock_user_schema, q='')
    assert result == []
    mock_user_service.search_users.assert_not_called()
