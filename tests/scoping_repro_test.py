import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from rssa_storage.rssadb.models.study_components import StudyStep
from rssa_storage.rssadb.repositories.study_components import StudyStepRepository

from rssa_api.data.services.study_components import StudyStepService


@pytest.mark.asyncio
async def test_study_step_scoping_query_construction():
    # Mock DB session
    db_session = AsyncMock()

    # Mock execute result to return something so it doesn't crash,
    # but we are interested in the query passed to it.
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db_session.execute.return_value = mock_result

    # Initialize service
    repo = StudyStepRepository(db_session)
    service = StudyStepService(repo)

    study_id = uuid.uuid4()

    # Call the method
    await service.get_items_for_owner_as_ordered_list(study_id, StudyStep)

    # Verify the query passed to db.execute
    call_args = db_session.execute.call_args
    assert call_args is not None, 'db.execute was not called'

    query = call_args[0][0]
    compiled_query = str(query.compile(compile_kwargs={'literal_binds': True}))

    # Check if the query contains the filtering by study_id
    # The UUID might be represented differently, so we check for the column name and value presence
    assert 'study_steps.study_id' in compiled_query
    # SQLAlchemy might format UUIDs without hyphens in literal binds
    assert str(study_id) in compiled_query or study_id.hex in compiled_query
