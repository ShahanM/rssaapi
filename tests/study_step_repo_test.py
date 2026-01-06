import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from rssa_api.data.repositories.study_components import StudyStepRepository
from rssa_api.data.models.study_components import StudyStep

@pytest.mark.asyncio
async def test_study_step_repo_crud():
    db_session = AsyncMock()
    repo = StudyStepRepository(db_session)
    
    # Create a mock StudyStep
    step_id = uuid.uuid4()
    step = StudyStep(
        id=step_id, 
        name="Original Name", 
        study_id=uuid.uuid4(),
        order_position=1,
        path="path"
    )
    
    # Test Update
    repo.find_one = AsyncMock(return_value=step)
    
    updated_step = await repo.update(step_id, {"name": "Updated Name"})
    
    assert updated_step is not None
    assert updated_step.name == "Updated Name"
    assert db_session.flush.called
    
    # Test Delete (Soft Delete)
    db_session.flush.reset_mock()
    
    deleted = await repo.delete(step_id)
    
    assert deleted is True
    assert step.deleted_at is not None
    assert db_session.flush.called
