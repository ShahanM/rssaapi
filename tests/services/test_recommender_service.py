import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.rssadb.repositories.participant_responses import (
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
)
from rssa_storage.rssadb.repositories.study_participants import StudyParticipantRepository

from rssa_api.data.schemas.recommendations import EnrichedRecResponse, StandardRecResponse
from rssa_api.services.recommendation.strategies import LambdaStrategy

# Mocking modules that might rely on AWS or DB connections if imported directly
# (Though in unit tests we usually mock the repository instances passed to the service)
from rssa_api.services.recommender_service import RecommenderService


@pytest.fixture
def mock_repos():
    return {
        'study_participant': AsyncMock(spec=StudyParticipantRepository),
        'participant_rating': AsyncMock(spec=ParticipantRatingRepository),
        'movie': AsyncMock(spec=MovieRepository),
        'interaction': AsyncMock(spec=ParticipantStudyInteractionResponseRepository),
        'context': AsyncMock(),
    }


@pytest.fixture
def recommender_service(mock_repos):
    return RecommenderService(
        study_participant_repository=mock_repos['study_participant'],
        participant_rating_repository=mock_repos['participant_rating'],
        movie_repository=mock_repos['movie'],
        participant_interaction_repository=mock_repos['interaction'],
        recommendation_context_repository=mock_repos['context'],
    )


@pytest.fixture
def mock_registry(monkeypatch):
    registry = {}
    monkeypatch.setattr('rssa_api.services.recommender_service.REGISTRY', registry)
    return registry


@pytest.mark.asyncio
async def test_get_recommendations_success(recommender_service, mock_repos, mock_registry):
    # Setup
    user_id = uuid.uuid4()
    algorithm_key = 'test_strategy'

    # Mock Participant
    mock_participant = MagicMock()
    mock_participant.study_condition.recommender_key = algorithm_key
    mock_repos['study_participant'].find_one.return_value = mock_participant

    # Mock Strategy in Registry
    mock_strategy = AsyncMock(spec=LambdaStrategy)
    expected_standard_response = StandardRecResponse(items=[101, 102], total_count=2)
    mock_strategy.recommend.return_value = expected_standard_response
    mock_registry[algorithm_key] = mock_strategy

    # Mock Ratings (History)
    mock_rating = MagicMock()
    mock_rating.item_id = 999
    mock_rating.rating = 5.0
    mock_repos['participant_rating'].find_many.return_value = [mock_rating]

    # Mock Movie Enricher
    mock_movie1 = MagicMock()
    mock_movie1.movielens_id = '101'
    # Attributes for validation if we weren't mocking schema, but we will mock schema validation

    mock_movie2 = MagicMock()
    mock_movie2.movielens_id = '102'

    # Return list of movie objects
    mock_repos['movie'].find_many.return_value = [mock_movie1, mock_movie2]

    # Mock Schema Validation to return a simple object or dict
    # We need to patch MovieSchema in the service module
    with patch('rssa_api.services.recommender_service.MovieDetailSchema') as MockMovieSchema:
        # Arrange Schema to return something valid
        def side_effect(obj):
            m = MagicMock()  # Return a mock that represents the schema
            m.movielens_id = obj.movielens_id
            return m

        MockMovieSchema.model_validate.side_effect = side_effect

        # Execution
        context_data = {'step_id': str(uuid.uuid4()), 'context_tag': 'test_tag'}
        result = await recommender_service.get_recommendations_for_study_participant(
            uuid.uuid4(), user_id, context_data
        )

    # Assertions
    assert isinstance(result, EnrichedRecResponse)
    assert len(result.recommendations) == 2
    assert result.total_count == 2
    # Verify Movies are correctly mapped?
    # Since we mocked schema validation inside the service, we might need to actually mock MovieSchema.model_validate or return proper objects
    # But let's assume the MagicMock works if attributes are accessed.
    # Actually, the service does: MovieSchema.model_validate(movie_map[mid])
    # So our mock_movie must be compatible with MovieSchema.model_validate or we mock MovieSchema.

    mock_repos['study_participant'].find_one.assert_called_once()
    mock_strategy.recommend.assert_called_once()
    assert mock_repos['movie'].find_many.call_count == 2


@pytest.mark.asyncio
async def test_get_recommendations_missing_strategy(recommender_service, mock_repos, mock_registry):
    user_id = uuid.uuid4()

    # Mock Participant with unknown strategy
    mock_participant = MagicMock()
    mock_participant.study_condition.recommender_key = 'unknown_algo'
    mock_repos['study_participant'].find_one.return_value = mock_participant

    # Registry is empty

    context_data = {'step_id': str(uuid.uuid4()), 'context_tag': 'test_tag'}
    with pytest.raises(ValueError, match='No strategy found'):
        await recommender_service.get_recommendations_for_study_participant(uuid.uuid4(), user_id, context_data)


@pytest.mark.asyncio
async def test_get_recommendations_verifies_eager_load(recommender_service, mock_repos, mock_registry):
    # Setup
    user_id = uuid.uuid4()
    algorithm_key = 'test_strategy_eager'

    # Mock Participant
    mock_participant = MagicMock()
    mock_participant.study_condition.recommender_key = algorithm_key  # Note: code uses recommender_key
    mock_repos['study_participant'].find_one.return_value = mock_participant

    # Mock Strategy
    mock_strategy = AsyncMock(spec=LambdaStrategy)
    expected_response = StandardRecResponse(items=[101], total_count=1)
    mock_strategy.recommend.return_value = expected_response
    mock_registry[algorithm_key] = mock_strategy

    # Mock Ratings
    mock_repos['participant_rating'].find_many.return_value = []

    # Mock Movies for history (empty)
    mock_repos['movie'].find_many.side_effect = [
        [],
        [MagicMock(movielens_id='101')],
    ]  # 1st call history, 2nd call enrichment

    with patch('rssa_api.services.recommender_service.MovieDetailSchema') as MockMovieSchema:
        # Execution
        context_data = {'step_id': str(uuid.uuid4()), 'context_tag': 'test_tag'}
        await recommender_service.get_recommendations_for_study_participant(uuid.uuid4(), user_id, context_data)

        # Assertions
        # Verify enrichment call used load_options
        call_args_list = mock_repos['movie'].find_many.call_args_list
        assert len(call_args_list) == 2

        # check 2nd call (enrichment)
        enrichment_call_arg = call_args_list[1][0][0]  # RepoQueryOptions object
        assert enrichment_call_arg.filters == {'movielens_id': ['101']}
        assert enrichment_call_arg.load_options is not None
        assert len(enrichment_call_arg.load_options) >= 1


@pytest.mark.asyncio
async def test_get_recommendations_records_interaction(recommender_service, mock_repos, mock_registry):
    # Setup
    user_id = uuid.uuid4()
    algorithm_key = 'test_strategy_interact'
    step_id = uuid.uuid4()

    # Mock Participant
    mock_participant = MagicMock()
    mock_participant.study_condition.recommender_key = algorithm_key
    mock_participant.id = user_id
    mock_participant.study_id = uuid.uuid4()
    mock_repos['study_participant'].find_one.return_value = mock_participant

    # Mock Strategy
    mock_strategy = AsyncMock(spec=LambdaStrategy)
    expected_response = StandardRecResponse(items=[], total_count=0)
    mock_strategy.recommend.return_value = expected_response
    mock_registry[algorithm_key] = mock_strategy

    # Mock Ratings (empty)
    mock_repos['participant_rating'].find_many.return_value = []

    # Mock Movies (empty)
    mock_repos['movie'].find_many.return_value = []

    # Case 1: New Interaction (interaction not found)
    mock_repos['interaction'].find_one.return_value = None

    context_data = {
        'emotion_input': [{'emotion': 'joy', 'weight': 'high'}],
        'step_id': str(step_id),
        'context_tag': 'emotion_tuning',
    }

    # Execution
    await recommender_service.get_recommendations_for_study_participant(
        mock_participant.study_id, user_id, context_data
    )

    # Assertions
    # Should check find_one called
    mock_repos['interaction'].find_one.assert_called_once()
    # Should check create called
    mock_repos['interaction'].create.assert_called_once()
    create_arg = mock_repos['interaction'].create.call_args[0][0]
    assert create_arg.context_tag == 'emotion_tuning'
    assert create_arg.study_step_id == step_id
    assert 'history' in create_arg.payload_json.extra
    assert len(create_arg.payload_json.extra['history']) == 1
    assert create_arg.payload_json.extra['history'][0]['emotion_input'] == context_data['emotion_input']


@pytest.mark.asyncio
async def test_get_recommendations_updates_interaction(recommender_service, mock_repos, mock_registry):
    # Setup
    user_id = uuid.uuid4()
    algorithm_key = 'test_strategy_interact_update'
    step_id = uuid.uuid4()

    # Mock Participant
    mock_participant = MagicMock()
    mock_participant.study_condition.recommender_key = algorithm_key
    mock_participant.id = user_id
    mock_participant.study_id = uuid.uuid4()
    mock_repos['study_participant'].find_one.return_value = mock_participant

    # Mock Strategy
    mock_strategy = AsyncMock(spec=LambdaStrategy)
    mock_strategy.recommend.return_value = StandardRecResponse(items=[], total_count=0)
    mock_registry[algorithm_key] = mock_strategy

    # Mock Ratings (empty)
    mock_repos['participant_rating'].find_many.return_value = []
    mock_repos['movie'].find_many.return_value = []

    # Case 2: Existing Interaction (interaction found)
    existing_mock = MagicMock()
    existing_mock.id = uuid.uuid4()
    existing_mock.payload_json = {'history': [{'timestamp': 'old', 'emotion_input': []}]}
    mock_repos['interaction'].find_one.return_value = existing_mock

    context_data = {
        'emotion_input': [{'emotion': 'sadness', 'weight': 'low'}],
        'step_id': str(step_id),
        'context_tag': 'emotion_tuning',
    }

    # Execution
    await recommender_service.get_recommendations_for_study_participant(
        mock_participant.study_id, user_id, context_data
    )

    # Assertions
    mock_repos['interaction'].find_one.assert_called_once()
    mock_repos['interaction'].update.assert_called_once()
    update_id, update_payload = mock_repos['interaction'].update.call_args[0]
    assert update_id == existing_mock.id
    assert 'history' in update_payload['payload_json']
    assert len(update_payload['payload_json']['history']) == 2  # 1 old + 1 new
