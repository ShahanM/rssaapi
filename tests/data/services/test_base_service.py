"""Tests for BaseService."""

import uuid
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel
from rssa_storage.shared import BaseRepository

from rssa_api.data.services.base_service import BaseService


class MockSchema(BaseModel):
    """Mock schema for testing."""

    id: uuid.UUID
    name: str

    model_config = {'from_attributes': True}


class MockModel:
    """Mock model for testing."""

    def __init__(self, id, name) -> None:
        """Initialize the mock model."""
        self.id = id
        self.name = name


class MockService(BaseService[MockModel, AsyncMock]):
    """Mock service for testing."""

    pass


@pytest.fixture
def mock_repo() -> AsyncMock:
    """Fixture for a mocked repository."""
    return AsyncMock(spec=BaseRepository)


@pytest.fixture
def service(mock_repo: AsyncMock) -> MockService:
    """Fixture for the MockService with a mocked repository."""
    service = MockService(mock_repo)
    mock_repo.model = MockModel
    return service


@pytest.mark.asyncio
async def test_create(service: MockService, mock_repo: AsyncMock) -> None:
    """Test creating a new resource."""
    schema = MockSchema(id=uuid.uuid4(), name='test')

    mock_repo.create.return_value = MockModel(schema.id, schema.name)

    result = await service.create(schema)

    assert result.name == 'test'
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id(service: MockService, mock_repo: AsyncMock) -> None:
    """Test retrieving a resource by ID."""
    uid = uuid.uuid4()
    mock_model = MockModel(uid, 'test')
    mock_repo.find_one.return_value = mock_model

    result_model = await service.get(uid)
    assert result_model == mock_model

    result_schema = await service.get(uid, schema=MockSchema)
    assert isinstance(result_schema, MockSchema)
    assert result_schema.id == uid


@pytest.mark.asyncio
async def test_get_detailed(service: MockService, mock_repo: AsyncMock) -> None:
    """Test retrieving a resource with detailed relationships loaded."""
    uid = uuid.uuid4()
    mock_model = MockModel(uid, 'detailed')
    mock_repo.find_one.return_value = mock_model

    service.repo.LOAD_FULL_DETAILS = ['rel']

    await service.get_detailed(uid)

    call_args = mock_repo.find_one.call_args[0][0]
    assert call_args.load_options == ['rel']


@pytest.mark.asyncio
async def test_update(service: MockService, mock_repo: AsyncMock) -> None:
    """Test updating a resource."""
    uid = uuid.uuid4()
    await service.update(uid, {'name': 'new'})
    mock_repo.update.assert_called_with(uid, {'name': 'new'})


@pytest.mark.asyncio
async def test_delete(service: MockService, mock_repo: AsyncMock) -> None:
    """Test deleting a resource."""
    uid = uuid.uuid4()
    await service.delete(uid)
    mock_repo.delete.assert_called_with(uid)


@pytest.mark.asyncio
async def test_get_paged_list(service: MockService, mock_repo: AsyncMock) -> None:
    """Test retrieving a paged list of resources with search."""
    mock_list = [MockModel(uuid.uuid4(), '1'), MockModel(uuid.uuid4(), '2')]
    mock_repo.find_many.return_value = mock_list

    service.repo.SEARCHABLE_COLUMNS = ['name']

    results = await service.get_paged_list(10, 0, search='1')
    assert len(results) == 2

    results_schema = await service.get_paged_list(10, 0, schema=MockSchema)
    assert len(results_schema) == 2
    assert isinstance(results_schema[0], MockSchema)

    call_args = mock_repo.find_many.call_args_list[0][0][0]
    assert call_args.search_text == '1'
    assert call_args.search_columns == ['name']


@pytest.mark.asyncio
async def test_count(service: MockService, mock_repo: AsyncMock) -> None:
    """Test counting resources matching a search query."""
    mock_repo.count.return_value = 5
    c = await service.count(search='test')
    assert c == 5
    mock_repo.count.assert_called_once()
