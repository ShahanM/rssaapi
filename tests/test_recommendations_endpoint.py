"""Tests for the recommendations endpoint."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from rssa_api.apps.study.main import api as study_api
from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.schemas.movie_schemas import EmotionsSchema, MovieDetailSchema
from rssa_api.data.schemas.recommendations import EnrichedResponseWrapper
from rssa_api.main import app
from rssa_api.services.dependencies import get_recommender_service
from rssa_api.services.recommender_service import RecommenderService


@pytest.mark.asyncio
async def test_recommendations_endpoint_returns_emotions(client: MagicMock, db_session: MagicMock) -> None:
    """Verifies that the recommendations endpoint correctly returns emotion data.

    This test mocks the RecommenderService and ensures the API response structure matches expectations.
    """
    # Setup Data
    study_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    # Mock Response
    mock_movie = MagicMock(spec=MovieDetailSchema)
    mock_movie.id = uuid.uuid4()
    mock_movie.movielens_id = '101'
    mock_movie.title = 'Test Movie'

    emotions = EmotionsSchema(
        id=uuid.uuid4(),
        movie_id=mock_movie.id,
        movielens_id='101',
        anger=0.1,
        anticipation=0.2,
        disgust=0.1,
        fear=0.1,
        joy=0.5,
        surprise=0.1,
        sadness=0.1,
        trust=0.1,
        iers_count=1,
        iers_rank=1,
    )

    movie_detail = MovieDetailSchema(
        id=mock_movie.id,
        movielens_id='101',
        title='Test Movie',
        year=2021,
        ave_rating=4.5,
        genre='Comedy',
        description='A funny movie',
        poster='path/to/poster',
        cast='Actor A',
        emotions=emotions,
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
        imdb_genres='Comedy',
        tmdb_genres='Comedy',
        imdb_popularity=1.0,
        tmdb_popularity=1.0,
    )

    # response_obj = EnrichedRecResponse(items=[movie_detail], total_count=1, response_type='standard')
    response_obj = EnrichedResponseWrapper(rec_type='standard', items={int(mock_movie.id): movie_detail})

    # Mock Service
    mock_service = AsyncMock(spec=RecommenderService)
    mock_service = AsyncMock(spec=RecommenderService)
    # The endpoint calls get_recommendations_for_study_participant, not get_recommendations
    mock_service.get_recommendations_for_study_participant.return_value = response_obj

    async def override_get_service():
        return mock_service

    async def override_validate(id_token: str = 'token'):
        return {'pid': uuid.UUID(user_id), 'sid': uuid.UUID(study_id)}

    # Apply overrides
    # Override on study_api since it is the sub-application handling the request
    study_api.dependency_overrides[get_recommender_service] = override_get_service
    study_api.dependency_overrides[validate_study_participant] = override_validate

    # Also override on app just in case (though study_api should be enough)
    app.dependency_overrides[get_recommender_service] = override_get_service
    app.dependency_overrides[validate_study_participant] = override_validate

    # Clear root_path like in studies_router_test.py
    app.root_path = ''

    try:
        # Action
        response = await client.post(
            '/study/recommendations/',
            json={'emotion_input': []},
            headers={
                'Authorization': 'Bearer testtoken',
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data['rec_type'] == 'standard'
        assert len(data['items']) == 1

        # Items is a dict keyed by movie ID
        items_dict = data['items']
        # Get the first item value
        item = list(items_dict.values())[0]

        assert item['movielens_id'] == '101'
        assert 'emotions' in item
        assert item['emotions']['joy'] == 0.5

    finally:
        app.dependency_overrides = {}
        study_api.dependency_overrides = {}
