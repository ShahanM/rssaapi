import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from rssa_api.data.models.study_components import StudyStepPageContent
from rssa_api.data.models.survey_constructs import SurveyConstruct, SurveyScale
from rssa_api.data.repositories.study_components import StudyStepPageContentRepository
from rssa_api.data.schemas.base_schemas import OrderedListItem

@pytest.mark.asyncio
async def test_study_step_page_content_name_property():
    # Create mock objects
    construct = SurveyConstruct(id=uuid.uuid4(), name="Test Construct", description="Desc")
    scale = SurveyScale(id=uuid.uuid4(), name="Test Scale")
    
    content = StudyStepPageContent(
        study_step_page_id=uuid.uuid4(),
        survey_construct_id=construct.id,
        survey_scale_id=scale.id,
        survey_construct=construct,
        survey_scale=scale,
        order_position=1
    )
    
    # Test property directly
    assert content.name == "Test Construct"
    
    # Test Pydantic validation
    # We need to mock the id because DBMixin expects it, but it's not in the init above (it's a mixin)
    # Actually DBMixin defines id field.
    content.id = uuid.uuid4()
    content.created_at = None
    content.updated_at = None
    content.created_by_id = uuid.uuid4()
    
    # OrderedListItem requires id, created_at, updated_at, created_by_id (from AuditMixin), order_position, name
    # We need to ensure content has these.
    
    # Mocking datetime for pydantic validation if needed, but None might be allowed if Optional?
    # AuditMixin: created_at: Optional[datetime], updated_at: Optional[datetime]
    
    schema_item = OrderedListItem.model_validate(content)
    assert schema_item.name == "Test Construct"
    assert schema_item.order_position == 1

@pytest.mark.asyncio
async def test_repo_uses_load_options():
    db_session = AsyncMock()
    repo = StudyStepPageContentRepository(db_session)
    
    # Mock find_many to return empty list
    repo.find_many = AsyncMock(return_value=[])
    
    await repo.get_all_ordered_instances(uuid.uuid4())
    
    # Verify find_many was called with options containing load_options
    call_args = repo.find_many.call_args
    assert call_args is not None
    options = call_args[0][0]
    assert options.load_options is not None
    assert len(options.load_options) > 0
