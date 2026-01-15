"""Tests for StudyAdmin related services."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rssa_storage.rssadb.repositories.study_admin import (
    ApiKeyRepository,
    UserRepository,
)

from rssa_api.data.schemas.study_components import ApiKeyRead
from rssa_api.data.services.study_admin import (
    ApiKeyService,
    UserService,
)

# --- ApiKeyService Tests ---


@pytest.fixture
def mock_apikey_repo() -> AsyncMock:
    """Fixture for mocked ApiKeyRepository."""
    return AsyncMock(spec=ApiKeyRepository)


@pytest.fixture
def apikey_service(mock_apikey_repo: AsyncMock) -> ApiKeyService:
    """Fixture for ApiKeyService."""
    service = ApiKeyService(mock_apikey_repo)
    return service


def test_generate_key_and_hash(apikey_service: ApiKeyService) -> None:
    """Test generation of API key pair (plaintext and hash)."""
    key, hashed = apikey_service.generate_key_and_hash()
    assert isinstance(key, str)
    assert isinstance(hashed, str)
    assert len(key) > 10


@pytest.mark.asyncio
async def test_create_api_key_for_study(apikey_service: ApiKeyService, mock_apikey_repo: AsyncMock) -> None:
    """Test creation of a new API key for a study."""
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()
    desc = 'Test Key'

    mock_new_key = MagicMock()
    mock_new_key.id = uuid.uuid4()
    mock_new_key.created_at = 'now'
    mock_new_key.user_id = user_id
    mock_new_key.study_id = study_id
    mock_new_key.description = desc
    mock_new_key.is_active = True
    mock_new_key.plain_text_key = 'plain'  # Not on SA model but added in service dict

    mock_apikey_repo.create.return_value = mock_new_key
    mock_apikey_repo.find_many.return_value = []  # no existing keys

    # We patch sa_obj_to_dict to return a dict that validates
    with patch('rssa_api.data.services.study_admin.sa_obj_to_dict') as mock_to_dict:
        mock_to_dict.return_value = {
            'id': uuid.uuid4(),
            'created_at': '2023-01-01T00:00:00',
            'user_id': user_id,
            'study_id': study_id,
            'description': desc,
            'is_active': True,
        }

        result = await apikey_service.create_api_key_for_study(study_id, desc, user_id)

        assert isinstance(result, ApiKeyRead)
        mock_apikey_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_validate_api_key(apikey_service: ApiKeyService, mock_apikey_repo: AsyncMock) -> None:
    """Test validation of an API key against its hash."""
    api_key_id = uuid.uuid4()
    secret = 'secret'

    mock_key = MagicMock()
    mock_key.hashed_key = 'hashed_secret'
    mock_apikey_repo.find_one.return_value = mock_key

    # We must mock Fernet to avoid needing real encryption matching ENCRYPTION_KEY
    with patch('rssa_api.data.services.study_admin.Fernet') as MockFernet:
        instance = MockFernet.return_value
        instance.decrypt.return_value = b'secret'  # matches secret

        result = await apikey_service.validate_api_key(api_key_id, secret)

        assert result == mock_key


# --- UserService Tests ---


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    """Fixture for mocked UserRepository."""
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_user_repo: AsyncMock) -> UserService:
    """Fixture for UserService."""
    return UserService(mock_user_repo)


@pytest.mark.asyncio
async def test_user_creation(user_service: UserService, mock_user_repo: AsyncMock) -> None:
    """Test user creation logic."""
    pass
