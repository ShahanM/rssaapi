"""Tests for the RecommenderService."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.rssadb.models.participant_responses import ParticipantRating
from rssa_storage.rssadb.models.study_participants import StudyParticipant
from rssa_storage.rssadb.repositories.participant_responses import (
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
)
from rssa_storage.rssadb.repositories.study_participants import StudyParticipantRepository

from rssa_api.data.schemas.movie_schemas import EmotionsSchema, MovieDetailSchema
from rssa_api.data.schemas.recommendations import (
    EnrichedResponseWrapper,
    ResponseWrapper,
)
from rssa_api.services.recommendation.strategies import LambdaStrategy
from rssa_api.services.recommender_service import RecommenderService


@pytest.fixture
def mock_repos() -> dict[str, AsyncMock]:
    """Provides a dictionary of mocked repositories."""
    return {
        'study_participant': AsyncMock(spec=StudyParticipantRepository),
        'participant_rating': AsyncMock(spec=ParticipantRatingRepository),
        'movie': AsyncMock(spec=MovieRepository),
        'interaction': AsyncMock(spec=ParticipantStudyInteractionResponseRepository),
        'context': AsyncMock(),
    }


@pytest.fixture
def recommender_service(mock_repos: dict[str, AsyncMock]) -> RecommenderService:
    """Initializes the RecommenderService with mocked repositories."""
    return RecommenderService(
        study_participant_repository=mock_repos['study_participant'],
        participant_rating_repository=mock_repos['participant_rating'],
        movie_repository=mock_repos['movie'],
        participant_interaction_repository=mock_repos['interaction'],
        recommendation_context_repository=mock_repos['context'],
        ttl_seconds=300,
    )


@pytest.fixture
def mock_registry(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Mocks the strategy registry to avoid external dependencies."""
    registry = {}
    monkeypatch.setattr('rssa_api.services.recommender_service.REGISTRY', registry)
    return registry


def create_dummy_movie_detail(mid: str) -> MovieDetailSchema:
    """Creates a dummy movie detail schema."""
    return MovieDetailSchema(
        id=uuid.uuid4(),
        movielens_id=mid,
        title=f'Movie {mid}',
        year=2000,
        ave_rating=4.0,
        genre='Action',
        description='Desc',
        poster='poster.jpg',
        cast='Cast',
        emotions=EmotionsSchema(
            id=uuid.uuid4(),
            movie_id=uuid.uuid4(),
            movielens_id=mid,
            anger=0.1,
            anticipation=0.1,
            disgust=0.1,
            fear=0.1,
            joy=0.1,
            sadness=0.1,
            surprise=0.1,
            trust=0.1,
            iers_count=1,
            iers_rank=1,
        ),
        imdb_id='tt123',
        tmdb_id='123',
        director='Director',
        writer='Writer',
        imdb_avg_rating=5.0,
        imdb_rate_count=100,
        tmdb_avg_rating=5.0,
        tmdb_rate_count=100,
        movielens_avg_rating=5.0,
        movielens_rate_count=100,
        origin_country='US',
        parental_guide='PG',
        movie_lens_dataset='25m',
        imdb_genres='Action',
        tmdb_genres='Action',
        imdb_popularity=1.0,
        tmdb_popularity=1.0,
    )


@pytest.mark.asyncio
async def test_get_recommendations_success(
    recommender_service: RecommenderService, mock_repos: dict[str, AsyncMock], mock_registry: dict[str, Any]
) -> None:
    """Verifies successful recommendation generation and enrichment."""
    # Setup
    study_id = uuid.uuid4()
    participant_id = uuid.uuid4()
    step_id = uuid.uuid4()
    context_tag = 'test_tag'
    algorithm_key = 'test_strategy'

    # Mock Participant
    mock_participant = MagicMock(spec=StudyParticipant)
    mock_participant.id = participant_id
    mock_participant.study_id = study_id
    mock_participant.study_condition.recommender_key = algorithm_key
    mock_participant.study_condition.recommendation_count = 10
    mock_repos['study_participant'].find_one.return_value = mock_participant

    # Mock Strategy
    mock_strategy = AsyncMock(spec=LambdaStrategy)
    expected_standard_response = ResponseWrapper(items=[101, 102], response_type='standard', total_count=2)
    mock_strategy.recommend.return_value = expected_standard_response
    mock_registry[algorithm_key] = mock_strategy

    # Mock Ratings (History)
    mock_rating = MagicMock(spec=ParticipantRating)
    mock_rating.item_id = 999
    mock_rating.rating = 5.0
    mock_repos['participant_rating'].find_many.return_value = [mock_rating]

    # No existing context
    mock_repos['context'].find_one.return_value = None
    context_data = {'step_id': str(step_id), 'context_tag': context_tag}

    # Mock Movie Enricher
    dummy_movie_101 = create_dummy_movie_detail('101')
    dummy_movie_102 = create_dummy_movie_detail('102')

    # The service calls: movies = await self.movie_repository.find_many(options)
    # Then: MovieDetailSchema.model_validate(movie)
    mock_repos['movie'].find_many.return_value = [dummy_movie_101, dummy_movie_102]

    # Execution
    result = await recommender_service.get_recommendations_for_study_participant(study_id, participant_id, context_data)

    # Assertions
    assert isinstance(result, EnrichedResponseWrapper)
    assert len(result.items) == 2
    assert 101 in result.items
    assert 102 in result.items

    mock_repos['study_participant'].find_one.assert_called_once()
    mock_strategy.recommend.assert_called_once()
    assert mock_repos['movie'].find_many.call_count > 0


@pytest.mark.asyncio
async def test_get_recommendations_missing_strategy(
    recommender_service: RecommenderService, mock_repos: dict[str, AsyncMock], mock_registry: dict[str, Any]
) -> None:
    """Verifies that an error is raised when the strategy is missing."""
    study_id = uuid.uuid4()
    participant_id = uuid.uuid4()
    context_tag = 'test_tag'

    # Mock Participant with unknown strategy
    mock_participant = MagicMock(spec=StudyParticipant)
    mock_participant.study_condition.recommender_key = 'unknown_algo'
    mock_repos['study_participant'].find_one.return_value = mock_participant
    mock_repos['context'].find_one.return_value = None

    context_data = {'step_id': str(uuid.uuid4()), 'context_tag': context_tag}

    with pytest.raises(ValueError, match='No strategy found for key: unknown_algo'):
        await recommender_service.get_recommendations_for_study_participant(study_id, participant_id, context_data)


@pytest.mark.asyncio
async def test_get_recommendations_verifies_eager_load(
    recommender_service: RecommenderService, mock_repos: dict[str, AsyncMock], mock_registry: dict[str, Any]
) -> None:
    """Verifies that movie details are eager loaded during enrichment."""
    # Setup
    user_id = uuid.uuid4()
    algorithm_key = 'test_strategy_eager'

    # Mock Participant
    mock_participant = MagicMock()
    mock_participant.study_condition.recommender_key = algorithm_key
    mock_repos['study_participant'].find_one.return_value = mock_participant
    mock_repos['context'].find_one.return_value = None  # Ensure no cache

    # Mock Strategy
    mock_strategy = AsyncMock(spec=LambdaStrategy)
    expected_response = ResponseWrapper(items=[101], response_type='standard', total_count=1)
    mock_strategy.recommend.return_value = expected_response
    mock_registry[algorithm_key] = mock_strategy

    # Mock Ratings
    mock_repos['participant_rating'].find_many.return_value = []

    # Mock Movies
    dummy_movie = create_dummy_movie_detail('101')
    mock_repos['movie'].find_many.side_effect = [
        [],  # history
        [dummy_movie],  # enrichment
    ]

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
async def test_get_recommendations_records_interaction(
    recommender_service: RecommenderService, mock_repos: dict[str, AsyncMock], mock_registry: dict[str, Any]
) -> None:
    """Verifies that participant interactions are recorded during recommendation."""
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
    expected_response = ResponseWrapper(items=[], response_type='standard', total_count=0)
    mock_strategy.recommend.return_value = expected_response
    mock_registry[algorithm_key] = mock_strategy

    # Mock Ratings (empty)
    mock_repos['participant_rating'].find_many.return_value = []

    # Ensure no context cache
    mock_repos['context'].find_one.return_value = None

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
    assert 'history' in create_arg.payload_json['extra']
    assert len(create_arg.payload_json['extra']['history']) == 1


@pytest.mark.asyncio
async def test_get_recommendations_updates_interaction(
    recommender_service: RecommenderService, mock_repos: dict[str, AsyncMock], mock_registry: dict[str, Any]
) -> None:
    """Verifies that existing participant interactions are updated."""
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
    mock_strategy.recommend.return_value = ResponseWrapper(items=[], response_type='standard', total_count=0)
    mock_registry[algorithm_key] = mock_strategy

    # Mock Ratings (empty)
    mock_repos['participant_rating'].find_many.return_value = []

    # Ensure no context cache
    mock_repos['context'].find_one.return_value = None

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
    assert len(update_payload['payload_json']['history']) == 2
