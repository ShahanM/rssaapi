"""Test users router UUID."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from rssa_api.apps.admin.routers.users import get_current_user_endpoint, get_user_profile_endpoint
from rssa_api.data.schemas import Auth0UserSchema, UserSchema


@pytest.mark.asyncio
async def test_get_current_user_endpoint() -> None:
    """Test getting current user endpoint."""
    mock_db_user = MagicMock(spec=UserSchema)
    mock_db_user.id = uuid.uuid4()

    result = await get_current_user_endpoint(mock_db_user)
    assert result == mock_db_user


@pytest.mark.asyncio
async def test_get_user_profile_endpoint_invalid_uuid() -> None:
    """Test getting user profile endpoint with invalid UUID."""
    mock_user = Auth0UserSchema(sub='auth0|123')
    mock_service = AsyncMock()

    with pytest.raises(HTTPException) as excinfo:
        await get_user_profile_endpoint('invalid-uuid', mock_user, mock_service)

    assert excinfo.value.status_code == 400
    assert 'UUID required' in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_user_profile_endpoint_valid_uuid_user_found() -> None:
    """Test getting user profile endpoint with valid UUID and user found."""
    user_id = uuid.uuid4()
    auth0_id = 'auth0|555'

    mock_user = Auth0UserSchema(sub='auth0|123')
    mock_service = AsyncMock()

    mock_local_user = MagicMock()
    mock_local_user.auth0_sub = auth0_id
    mock_service.get_user_by_id.return_value = mock_local_user

    with patch('rssa_api.apps.admin.routers.users.get_user_profile_by_id', new_callable=AsyncMock) as mock_get_profile:
        # Case 1: Profile found
        mock_get_profile.return_value = {'name': 'Test User'}
        result = await get_user_profile_endpoint(str(user_id), mock_user, mock_service)
        assert result == {'name': 'Test User'}

        # Case 2: Profile not found
        mock_get_profile.return_value = None
        with pytest.raises(HTTPException) as excinfo:
            await get_user_profile_endpoint(str(user_id), mock_user, mock_service)
        assert excinfo.value.status_code == 404
        assert 'User profile not found' in excinfo.value.detail
