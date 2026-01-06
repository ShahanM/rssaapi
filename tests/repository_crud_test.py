import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from rssa_api.data.repositories.base_repo import BaseRepository
from rssa_api.data.models.rssa_base_models import DBBaseModel
from sqlalchemy.orm import Mapped, mapped_column

# Mock Model
class MockModel(DBBaseModel):
    __tablename__ = 'mock_model'
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)

@pytest.mark.asyncio
async def test_repository_crud_operations():
    db_session = AsyncMock()
    repo = BaseRepository(db_session, model=MockModel)
    
    # Test Create (Exists)
    instance = MockModel(name="Test")
    await repo.create(instance)
    assert db_session.add.called
    
    # Test Update (Implemented)
    # Mock find_one to return the instance
    repo.find_one = AsyncMock(return_value=instance)
    
    updated = await repo.update(instance.id, {"name": "Updated"})
    assert updated is not None
    assert updated.name == "Updated"
    assert db_session.flush.called

    # Test Delete (Implemented - Soft Delete)
    # Reset flush mock
    db_session.flush.reset_mock()
    
    deleted = await repo.delete(instance.id)
    assert deleted is True
    assert instance.deleted_at is not None
    assert db_session.flush.called
    
    # Test Delete (Implemented - Hard Delete)
    # Create a model without deleted_at
    class HardDeleteModel(DBBaseModel):
        __tablename__ = 'hard_delete_model'
        id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
        name: Mapped[str] = mapped_column()
        
    repo_hard = BaseRepository(db_session, model=HardDeleteModel)
    instance_hard = HardDeleteModel(name="Hard")
    repo_hard.find_one = AsyncMock(return_value=instance_hard)
    
    deleted_hard = await repo_hard.delete(instance_hard.id)
    assert deleted_hard is True
    assert db_session.delete.called
    assert db_session.flush.called
