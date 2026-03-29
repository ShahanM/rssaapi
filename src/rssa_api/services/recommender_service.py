"""Service for handling recommendation logic."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, cast

from rssa_storage.moviedb.repositories import MovieRepository
from rssa_storage.rssadb.models.study_participants import ParticipantRecommendationContext
from rssa_storage.rssadb.repositories.participant_responses import (
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponse,
    ParticipantStudyInteractionResponseRepository,
)
from rssa_storage.rssadb.repositories.study_participants import (
    ParticipantRecommendationContextRepository,
    StudyParticipantRepository,
)
from rssa_storage.shared import RepoQueryOptions

from rssa_api.data.schemas.movie_schemas import MovieDetailSchema
from rssa_api.data.schemas.participant_response_schemas import (
    DynamicPayload,
    MovieLensRating,
)
from rssa_api.data.schemas.recommendations import (
    AdvisorRecItem,
    Avatar,
    CommunityScoreRecItem,
    EnrichedAdvisorRecItem,
    EnrichedCommunityScoreItem,
    EnrichedRecUnionType,
    EnrichedResponseWrapper,
    ResponseWrapper,
)

from .recommendation.registry import REGISTRY

log = logging.getLogger(__name__)

AVATARS = {
    'cow': {
        'src': 'cow',
        'alt': 'An image of a cow representing Anonymous Cow',
        'name': 'Anonymous Cow',
    },
    'duck': {
        'src': 'duck',
        'alt': 'An image of a duck representing Anonymous Duck',
        'name': 'Anonymous Duck',
    },
    'elephant': {
        'src': 'elephant',
        'alt': 'An image of an elephant representing Anonymous Elephant',
        'name': 'Anonymous Elephant',
    },
    'zebra': {
        'src': 'zebra',
        'alt': 'An image of a zebra representing Anonymous Zebra',
        'name': 'Anonymous Zebra',
    },
    'llama': {
        'src': 'llama',
        'alt': 'An image of a llama representing Anonymous Llama',
        'name': 'Anonymous Llama',
    },
    'fox': {
        'src': 'fox',
        'alt': 'An image of a fox representing Anonymous Fox',
        'name': 'Anonymous Fox',
    },
    'tiger': {
        'src': 'tiger',
        'alt': 'An image of a tiger representing Anonymous Tiger',
        'name': 'Anonymous Tiger',
    },
}


class RecommenderService:
    """Service for handling recommendation logic."""

    def __init__(
        self,
        study_participant_repository: StudyParticipantRepository,
        participant_rating_repository: ParticipantRatingRepository,
        movie_repository: MovieRepository,
        participant_interaction_repository: ParticipantStudyInteractionResponseRepository,
        recommendation_context_repository: ParticipantRecommendationContextRepository,
        ttl_seconds: int = 300,
    ):
        self.study_participant_repository = study_participant_repository
        self.participant_rating_repository = participant_rating_repository
        self.movie_repository = movie_repository
        self.participant_interaction_repository = participant_interaction_repository
        self.recommendation_context_repository = recommendation_context_repository

        self.ttl = ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}  # caching results for ttl seconds
        self._in_flight: dict[str, asyncio.Future] = {}  # caching currently running tasks
        self._bg_tasks: set[asyncio.Task] = set()  # For fire-and-forget database calls

    async def get_recommendations(
        self, ratings: list[MovieLensRating], limit: int, context_data: dict[str, Any] | None = None
    ) -> EnrichedResponseWrapper:
        """Get recommendations based on ratings."""
        if not context_data:
            # TODO: This will return the implicit top N.
            return []
        # TODO: This should be a generic call to the recommender without needing participant context. The idea is for
        # this method to service the demo endpoints.
        return ResponseWrapper(response_type='standard', items=[])

    async def get_recommendations_for_study_participant(
        self, study_id: uuid.UUID, study_participant_id: uuid.UUID, context_data: dict[str, Any]
    ) -> EnrichedResponseWrapper:
        """Get recommendations for a study participant."""
        step_id, context_tag, step_page_id = self._parse_recommendation_context(context_data)

        # Check for previously generated recommendations (Cache/Persistence)
        existing_result = await self._get_existing_recommendations(study_id, study_participant_id, context_tag)
        if existing_result:
            return await self._process_recommendation_result(existing_result)

        dedup_key = f'{study_participant_id}_{context_tag}'
        if dedup_key in self._in_flight:
            log.info(f'Intercepted concurrent request. Joining in-flight generation for {dedup_key}')
            raw_result = await self._in_flight[dedup_key]
            return await self._process_recommendation_result(raw_result)
        gen_task = asyncio.create_task(
            self._generate_and_background_save(
                study_id, step_id, step_page_id, study_participant_id, context_tag, context_data
            )
        )
        self._in_flight[dedup_key] = gen_task

        try:
            raw_result = await gen_task
        finally:
            self._in_flight.pop(dedup_key, None)

        return await self._process_recommendation_result(raw_result)

    async def _getnerate_and_background_save(
        self,
        study_id: uuid.UUID,
        step_id: uuid.UUId,
        step_page_id: uuid.UUId | None,
        study_participant_id: uuid.UUID,
        context_tag: str,
        context_data: dict[str, Any],
    ) -> ResponseWrapper:
        """Handles parallel data fetching, algorithm execution, and backgrounding side-effects."""
        # Gather participant configuration and historical ratings
        config_task = self._get_participant_algorithm_config(study_participant_id)
        ratings_task = self._get_translated_participant_ratings(study_participant_id)
        (algorithm_key, limit), ratings = await asyncio.gather(config_task, ratings_task)

        # Handle Side Effects (Tracking interactions)
        if context_data.get('emotion_input'):
            self._fire_and_forget(self._upsert_interaction(study_id, study_participant_id, context_data))

        # Generate new recommendations
        strategy = REGISTRY.get(algorithm_key)
        if not strategy:
            raise ValueError(f'No strategy found for key: {algorithm_key}')

        try:
            result = await strategy.recommend(
                user_id=str(study_participant_id), ratings=ratings, limit=limit, run_config=context_data
            )
        except Exception as e:
            log.error(f'Error for {study_participant_id} [{algorithm_key}]: {e}')
            raise

        self._fire_and_forget(
            self._save_recommendation_context(
                study_id, step_id, step_page_id, study_participant_id, context_tag, result
            )
        )

        return await self._process_recommendation_result(result)

    def _parse_recommendation_context(self, context_data: dict[str, Any]) -> tuple[uuid.UUID, str, uuid.UUID | None]:
        """Extracts and validates required context fields."""
        step_id = context_data.get('step_id')
        context_tag = context_data.get('context_tag')
        step_page_id = context_data.get('step_page_id')

        if not step_id or not context_tag:
            raise ValueError('Step ID and context tag are required')

        return (uuid.UUID(str(step_id)), str(context_tag), uuid.UUID(str(step_page_id)) if step_page_id else None)

    async def _get_existing_recommendations(
        self, study_id: uuid.UUID, study_participant_id: uuid.UUID, context_tag: str
    ) -> ResponseWrapper | None:
        """Checks the database for previously generated recommendations for this context."""
        existing_ctx = await self.recommendation_context_repository.find_one(
            RepoQueryOptions(
                filters={
                    'study_participant_id': study_participant_id,
                    'study_id': study_id,
                    'context_tag': context_tag,
                }
            )
        )
        if existing_ctx:
            log.info(f'Found existing context for {study_id} {study_participant_id} {context_tag}')
            return ResponseWrapper.model_validate(existing_ctx.recommendations_json)

        log.info(f'No existing context found for {study_id} {study_participant_id} {context_tag}')
        return None

    async def _get_participant_algorithm_config(self, study_participant_id: uuid.UUID) -> tuple[str, int]:
        """Retrieves the assigned recommendation algorithm and limit for a participant."""
        participant = await self.study_participant_repository.find_one(
            RepoQueryOptions(
                ids=[study_participant_id], load_options=StudyParticipantRepository.LOAD_ASSIGNED_CONDITION
            )
        )
        if not participant or not participant.study_condition:
            raise ValueError('Participant or Condition not found')

        algorithm_key = participant.study_condition.recommender_key
        if algorithm_key is None:
            raise ValueError(f'No recommender specified for study_condition: {participant.study_condition.name}')

        return algorithm_key, participant.study_condition.recommendation_count

    async def _get_translated_participant_ratings(self, study_participant_id: uuid.UUID) -> list[MovieLensRating]:
        """Fetches participant ratings and maps internal UUIDs to external MovieLens IDs."""
        ratings_models = await self.participant_rating_repository.find_many(
            RepoQueryOptions(filters={'study_participant_id': study_participant_id})
        )

        if not ratings_models:
            return []

        # Fetch movies to get the MovieLens IDs
        movies = await self.movie_repository.find_many(RepoQueryOptions(ids=[r.item_id for r in ratings_models]))
        movie_map = {m.id: m.movielens_id for m in movies}

        ratings = []
        for r in ratings_models:
            if r.item_id in movie_map:
                ratings.append(MovieLensRating(item_id=movie_map[r.item_id], rating=r.rating))
            else:
                log.warning(f'Rating for item {r.item_id} skipped: Movie not found in DB')

        return ratings

    def _fire_and_forget(self, coro):
        """Safely executes a task in the background without garbage collection risk."""
        task = asyncio.create_task(coro)
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)

    async def _save_recommendation_context(
        self,
        study_id: uuid.UUID,
        step_id: uuid.UUID,
        step_page_id: uuid.UUID | None,
        study_participant_id: uuid.UUID,
        context_tag: str,
        result: ResponseWrapper,
    ) -> None:
        """Persists the newly generated recommendations to the database."""
        rec_ctx = ParticipantRecommendationContext(
            study_id=study_id,
            study_step_id=step_id,
            study_step_page_id=step_page_id,
            study_participant_id=study_participant_id,
            context_tag=context_tag,
            recommendations_json=result.model_dump(),
        )
        await self.recommendation_context_repository.create(rec_ctx)

    async def _process_recommendation_result(self, result: ResponseWrapper) -> EnrichedResponseWrapper:
        response_items: EnrichedRecUnionType
        if result.response_type == 'standard':
            # TODO: Check if we should use OrderedDict here or does dict in Python3 maintain order?
            movies = await self._enrich_with_moviedata([cast(str, rec_item) for rec_item in result.items])
            response_items = {int(movie.movielens_id): movie for movie in movies}

        elif result.response_type == 'community_advisors':
            response_items = await self._enrich_advisor_response(result)

        elif result.response_type == 'community_comparison':
            response_items = await self._enrich_pref_viz_response(result)
        else:
            raise KeyError('Result response_type key did not match any known types.')

        return EnrichedResponseWrapper(rec_type=result.response_type, items=response_items)

    async def _enrich_advisor_response(self, response: ResponseWrapper) -> EnrichedRecUnionType:
        """Helper to hydrate Advisor responses with movie data."""
        advisor_dict = {}
        all_movie_ids = set()
        advisors = []
        for advisor in response.items:
            advisor = cast(AdvisorRecItem, advisor)
            advisors.append(advisor)
            all_movie_ids.update([str(mid) for mid in advisor.profile_top_n])
            all_movie_ids.add(str(advisor.recommendation))

        all_movies = await self._enrich_with_moviedata(list(all_movie_ids))
        movie_dict = {str(m.movielens_id): m for m in all_movies}
        avatar_keys = list(AVATARS.keys())
        for i, advisor in enumerate(advisors):
            advisor_dict[advisor.id] = EnrichedAdvisorRecItem(
                id=advisor.id,
                recommendation=movie_dict[str(advisor.recommendation)],
                avatar=Avatar.model_validate(AVATARS[avatar_keys[i % len(avatar_keys)]]),
                profile_top_n=[movie_dict[str(rec)] for rec in advisor.profile_top_n],
            )
        return advisor_dict

    async def _enrich_pref_viz_response(self, response: ResponseWrapper) -> EnrichedRecUnionType:
        """Helper to hydrate Preference Visualization responses with movie data."""
        all_rec_ids = set()
        comm_scores = []
        log.info(f'ITEM LENGTH {len(response.items)}')
        for score_item in response.items:
            score_item = cast(CommunityScoreRecItem, score_item)
            comm_scores.append(score_item)
            all_rec_ids.add(score_item.item)

        movies = await self._enrich_with_moviedata([str(mid) for mid in all_rec_ids])
        movies_dict = {int(m.movielens_id): m for m in movies}
        return {
            score_item.item: EnrichedCommunityScoreItem(
                item=movies_dict[int(score_item.item)], **score_item.model_dump(exclude={'item'})
            )
            for score_item in comm_scores
        }

    async def _enrich_with_moviedata(self, movielens_ids: list[str]) -> list[MovieDetailSchema]:
        """Helper to enrich recommendations with movie data."""
        movielens_ids = [str(mid) for mid in movielens_ids]
        options = RepoQueryOptions(filters={'movielens_id': movielens_ids}, load_options=MovieRepository.LOAD_ALL)
        movies = await self.movie_repository.find_many(options)
        movie_map = {movie.movielens_id: MovieDetailSchema.model_validate(movie) for movie in movies}

        return [movie_map[mid] for mid in movielens_ids]  # we must preserve original order, since they are ranked

    async def _upsert_interaction(self, study_id: uuid.UUID, study_participant_id: uuid.UUID, context_data: dict):
        """Helper to upsert participant interactions."""
        try:
            step_id_str = context_data.get('step_id')
            if step_id_str:
                step_id = uuid.UUID(str(step_id_str))
                context_tag = context_data.get('tuning_tag', 'emotion_tuning')

                # Check for existing interaction
                existing_interaction = await self.participant_interaction_repository.find_one(
                    RepoQueryOptions(
                        filters={
                            'study_participant_id': study_participant_id,
                            'context_tag': context_tag,
                            'study_step_id': step_id,
                        }
                    )
                )

                new_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'emotion_input': context_data['emotion_input'],
                }

                if existing_interaction:
                    current_payload = existing_interaction.payload_json
                    history = current_payload.get('history', [])
                    if not isinstance(history, list):
                        history = []
                    history.append(new_entry)

                    updated_payload = {**current_payload, 'history': history}
                    await self.participant_interaction_repository.update(
                        existing_interaction.id, {'payload_json': updated_payload}
                    )
                else:
                    payload = ParticipantStudyInteractionResponse(
                        study_id=study_id,
                        study_participant_id=study_participant_id,
                        study_step_id=step_id,
                        context_tag=context_tag,
                        payload_json=DynamicPayload(extra={'history': [new_entry]}).model_dump(),
                    )
                    await self.participant_interaction_repository.create(payload)

        except Exception as e:
            log.error(f'Failed to record interaction: {e}')
