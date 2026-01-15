"""Tests for ParticipantResponseService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from rssa_storage.rssadb.repositories.participant_responses import (
    ParticipantFreeformResponseRepository,
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
    ParticipantSurveyResponseRepository,
)
from rssa_storage.rssadb.repositories.study_participants import StudyParticipantRepository

from rssa_api.data.services.response_service import ParticipantResponseService


@pytest.fixture
def mock_repos() -> dict[str, AsyncMock]:
    """Fixture providing mocked repositories for data access."""
    return {
        'participant': AsyncMock(spec=StudyParticipantRepository),
        'survey': AsyncMock(spec=ParticipantSurveyResponseRepository),
        'text': AsyncMock(spec=ParticipantFreeformResponseRepository),
        'rating': AsyncMock(spec=ParticipantRatingRepository),
        'interaction': AsyncMock(spec=ParticipantStudyInteractionResponseRepository),
    }


@pytest.fixture
def service(mock_repos: dict[str, AsyncMock]) -> ParticipantResponseService:
    """Fixture initializing the ParticipantResponseService with mocked repos."""
    return ParticipantResponseService(
        particpant_repo=mock_repos['participant'],
        item_response_repo=mock_repos['survey'],
        text_response_repo=mock_repos['text'],
        content_rating_repo=mock_repos['rating'],
        interact_response_repo=mock_repos['interaction'],
    )


def test_get_strategy(service: ParticipantResponseService, mock_repos: dict[str, AsyncMock]) -> None:
    """Test that _get_strategy returns the correct repository and schema for each ResponseType."""
    # Test internal _get_strategy logic
    # Use enum values or correct string values
    repo, schema = service._get_strategy('survey_item')
    assert repo == mock_repos['survey']

    repo, schema = service._get_strategy('text_response')
    assert repo == mock_repos['text']

    repo, schema = service._get_strategy('content_rating')
    assert repo == mock_repos['rating']

    repo, schema = service._get_strategy('study_interaction')
    assert repo == mock_repos['interaction']

    with pytest.raises(ValueError):
        service._get_strategy('unknown')


@pytest.mark.asyncio
async def test_get_response_for_page(service: ParticipantResponseService, mock_repos: dict[str, AsyncMock]) -> None:
    """Test retrieving responses for a specific study step page."""
    study_id = uuid.uuid4()
    participant_id = uuid.uuid4()
    page_id = uuid.uuid4()

    mock_res = MagicMock()
    mock_res.id = uuid.uuid4()
    mock_res.study_id = study_id
    mock_res.study_participant_id = participant_id
    mock_res.study_step_id = uuid.uuid4()
    mock_res.study_step_page_id = page_id
    mock_res.survey_construct_id = uuid.uuid4()
    mock_res.survey_item_id = uuid.uuid4()
    mock_res.survey_scale_id = uuid.uuid4()
    mock_res.survey_scale_level_id = uuid.uuid4()
    mock_res.context_tag = 'tag'
    mock_res.created_at = 'now'  # or datetime
    mock_res.updated_at = 'now'
    mock_res.discarded = False

    mock_repos['survey'].find_many.return_value = [mock_res]

    result = await service.get_response_for_page('survey_item', study_id, participant_id, page_id)
    assert len(result) == 1
    assert result[0].id == mock_res.id


@pytest.mark.asyncio
async def test_create_response(service: ParticipantResponseService, mock_repos: dict[str, AsyncMock]) -> None:
    """Test creating a new participant response."""
    study_id = uuid.uuid4()
    participant_id = uuid.uuid4()

    mock_data = MagicMock()
    mock_repos['survey'].create.return_value = 'created'

    # TODO: Needs correct attributes for singledispatch logic.
    pass


@pytest.mark.asyncio
async def test_update_response(service: ParticipantResponseService, mock_repos: dict[str, AsyncMock]) -> None:
    """Test updating an existing participant response."""
    # FIXME: We need to mock the update_response method for each repository.
    uid = uuid.uuid4()
    update_dict = {'val': 1}

    mock_repos['survey'].update_response.return_value = 'updated'

    await service.update_response('survey_item', uid, update_dict, client_version=1)

    mock_repos['survey'].update_response.assert_called_with(uid, update_dict, 1)
