"""Test study service authorizations."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from rssa_storage.rssadb.models.study_components import Study, StudyAuthorization

from rssa_api.data.services.study_components import StudyService


@pytest.fixture
def mock_study_repo() -> AsyncMock:
    """Mock study repository."""
    return AsyncMock()


@pytest.fixture
def mock_auth_repo() -> AsyncMock:
    """Mock study authorization repository."""
    return AsyncMock()


@pytest.fixture
def study_service(mock_study_repo: AsyncMock, mock_auth_repo: AsyncMock) -> StudyService:
    """Mock study service."""
    return StudyService(mock_study_repo, mock_auth_repo)


@pytest.mark.asyncio
async def test_check_study_access_owner(
    study_service: StudyService, mock_study_repo: AsyncMock, mock_auth_repo: AsyncMock
) -> None:
    """Test study access check for owner."""
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_study = MagicMock(spec=Study)
    mock_study.owner_id = user_id
    mock_study_repo.find_one.return_value = mock_study

    result = await study_service.check_study_access(study_id, user_id)

    assert result is True
    # Should check owner first and return True without checking auth repo
    mock_auth_repo.find_one.assert_not_called()


@pytest.mark.asyncio
async def test_check_study_access_authorized_user(
    study_service: StudyService,
    mock_study_repo: AsyncMock,
    mock_auth_repo: AsyncMock,
) -> None:
    """Test study access check for authorized user."""
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    mock_study = MagicMock(spec=Study)
    mock_study.owner_id = owner_id
    mock_study_repo.find_one.return_value = mock_study

    mock_auth_record = MagicMock(spec=StudyAuthorization)
    mock_auth_repo.find_one.return_value = mock_auth_record

    result = await study_service.check_study_access(study_id, user_id)

    assert result is True
    mock_auth_repo.find_one.assert_called_once()


@pytest.mark.asyncio
async def test_check_study_access_unauthorized(
    study_service: StudyService, mock_study_repo: AsyncMock, mock_auth_repo: AsyncMock
) -> None:
    """Test study access check for unauthorized user."""
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    mock_study = MagicMock(spec=Study)
    mock_study.owner_id = owner_id
    mock_study_repo.find_one.return_value = mock_study

    mock_auth_repo.find_one.return_value = None

    result = await study_service.check_study_access(study_id, user_id)

    assert result is False


@pytest.mark.asyncio
async def test_add_study_authorization(study_service: StudyService, mock_auth_repo: AsyncMock) -> None:
    """Test adding a study authorization."""
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()
    role = 'editor'

    await study_service.add_study_authorization(study_id, user_id, role)

    mock_auth_repo.create.assert_called_once()
    args, _ = mock_auth_repo.create.call_args
    auth_obj = args[0]
    assert auth_obj.study_id == study_id
    assert auth_obj.user_id == user_id
    assert auth_obj.role == role


@pytest.mark.asyncio
async def test_remove_study_authorization(study_service: StudyService, mock_auth_repo: AsyncMock) -> None:
    """Test removing a study authorization."""
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_auth = MagicMock(spec=StudyAuthorization)
    mock_auth.id = uuid.uuid4()
    mock_auth_repo.find_one.return_value = mock_auth

    await study_service.remove_study_authorization(study_id, user_id)

    mock_auth_repo.find_one.assert_called_once()
    mock_auth_repo.delete.assert_called_with(mock_auth.id)


@pytest.mark.asyncio
async def test_check_study_access_min_role_success(
    study_service: StudyService, mock_study_repo: AsyncMock, mock_auth_repo: AsyncMock
) -> None:
    """Test access when user role meets min_role requirement."""
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    mock_study = MagicMock(spec=Study)
    mock_study.owner_id = owner_id
    mock_study_repo.find_one.return_value = mock_study

    # User is admin, min_role is editor. 2 >= 1 => True
    mock_auth_record = MagicMock(spec=StudyAuthorization)
    mock_auth_record.role = 'admin'
    mock_auth_repo.find_one.return_value = mock_auth_record

    result = await study_service.check_study_access(study_id, user_id, min_role='editor')
    assert result is True


@pytest.mark.asyncio
async def test_check_study_access_min_role_failure(
    study_service: StudyService, mock_study_repo: AsyncMock, mock_auth_repo: AsyncMock
) -> None:
    """Test access denial when user role is insufficient."""
    study_id = uuid.uuid4()
    user_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    mock_study = MagicMock(spec=Study)
    mock_study.owner_id = owner_id
    mock_study_repo.find_one.return_value = mock_study

    # User is viewer, min_role is editor. 0 >= 1 => False
    mock_auth_record = MagicMock(spec=StudyAuthorization)
    mock_auth_record.role = 'viewer'
    mock_auth_repo.find_one.return_value = mock_auth_record

    result = await study_service.check_study_access(study_id, user_id, min_role='editor')
    assert result is False
