"""Tests reproducing specific service behaviors."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from rssa_storage.rssadb.models.rssa_base_models import RssaBase as DBBaseModel
from rssa_storage.rssadb.models.rssa_base_models import RssaOrderedBase as DBBaseOrderedModel
from rssa_storage.shared import BaseOrderedRepository, BaseRepository
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from rssa_api.data.services.base_ordered_service import BaseOrderedService
from rssa_api.data.services.base_scoped_service import BaseScopedService


# Mock Models
class MockModel(DBBaseModel):
    __tablename__ = 'mock_model'
    __table_args__ = {'extend_existing': True}
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)


class MockOrderedModel(DBBaseOrderedModel):
    __tablename__ = 'mock_ordered_model'
    __table_args__ = {'extend_existing': True}
    parent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)


# Mock Repositories
class MockRepo(BaseRepository[MockModel]):
    pass


class MockOrderedRepo(BaseOrderedRepository[MockOrderedModel]):
    parent_id_column_name = 'parent_id'


# Mock Services
class MockScopedService(BaseScopedService[MockModel, MockRepo]):
    scope_field = 'owner_id'


class MockOrderedService(BaseOrderedService[MockOrderedModel, MockOrderedRepo]):
    pass


@pytest.mark.asyncio
async def test_base_scoped_service_methods() -> None:
    """Verifies base scoped service methods (get_for_owner, paged, etc)."""
    db = AsyncMock()
    # Mock db.execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = MockModel()
    mock_result.scalars.return_value.all.return_value = [MockModel()]
    db.execute.return_value = mock_result

    repo = MockRepo(db, MockModel)
    service = MockScopedService(repo)

    # Test get_for_owner
    await service.get_for_owner(uuid.uuid4(), uuid.uuid4())

    # Test get_paged_for_owner
    await service.get_paged_for_owner(uuid.uuid4(), 10, 0)

    # Test get_all_for_owner
    await service.get_all_for_owner(uuid.uuid4())


@pytest.mark.asyncio
async def test_base_ordered_service_methods() -> None:
    """Verifies base ordered service methods (create_for_owner, get ordered list)."""
    db = AsyncMock()

    db.add = MagicMock()

    # Mock db.execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = MockOrderedModel(order_position=1)
    mock_result.scalars.return_value.all.return_value = [MockOrderedModel(order_position=1)]
    mock_result.scalar_one_or_none.return_value = MockOrderedModel(order_position=1)
    db.execute.return_value = mock_result

    repo = MockOrderedRepo(db, MockOrderedModel)
    service = MockOrderedService(repo)

    # Test create_for_owner
    await service.create_for_owner(uuid.uuid4(), MagicMock())

    # Test get_items_for_owner_as_ordered_list
    await service.get_items_for_owner_as_ordered_list(uuid.uuid4())
