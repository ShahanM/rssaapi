import json
import logging
import uuid
from datetime import datetime
from random import shuffle
from re import M
from typing import Optional, cast

from sqlalchemy.orm import joinedload

from rssa_api.data.models.participant_responses import ParticipantStudyInteractionResponse
from rssa_api.data.models.study_participants import ParticipantRecommendationContext, StudyParticipant
from rssa_api.data.repositories.base_repo import RepoQueryOptions
from rssa_api.data.repositories.items.movies import MovieRepository
from rssa_api.data.repositories.participant_responses import (
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
)
from rssa_api.data.repositories.study_participants.recommendation_context import (
    ParticipantRecommendationContextRepository,
)
from rssa_api.data.repositories.study_participants.study_participants import StudyParticipantRepository
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
    RecommendationResponse,
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
        'alt': 'An image of a dox representing Anonymous Fox',
        'name': 'Anonymous Fox',
    },
    'tiger': {
        'src': 'tiger',
        'alt': 'An image of a tiger representing Anonymous Tiger',
        'name': 'Anonymous Tiger',
    },
}


class RecommenderService:
    def __init__(
        self,
        study_participant_repository: StudyParticipantRepository,
        participant_rating_repository: ParticipantRatingRepository,
        movie_repository: MovieRepository,
        participant_interaction_repository: ParticipantStudyInteractionResponseRepository,
        recommendation_context_repository: ParticipantRecommendationContextRepository,
    ):
        self.study_participant_repository = study_participant_repository
        self.participant_rating_repository = participant_rating_repository
        self.movie_repository = movie_repository
        self.participant_interaction_repository = participant_interaction_repository
        self.recommendation_context_repository = recommendation_context_repository

    async def get_recommendations(
        self, study_id: uuid.UUID, study_participant_id: uuid.UUID, context_data: Optional[dict] = None
    ) -> RecommendationResponse:
        step_id = None
        context_tag = None
        step_page_id = None

        if context_data:
            step_id_str = context_data.get('step_id')
            if step_id_str:
                step_id = uuid.UUID(str(step_id_str))

            context_tag = context_data.get('context_tag')
            step_page_id_str = context_data.get('step_page_id')
            if step_page_id_str:
                step_page_id = uuid.UUID(str(step_page_id_str))

        result = None
        if step_id and context_tag:
            existing_ctx = await self.recommendation_context_repository.find_one(
                RepoQueryOptions(
                    filters={
                        'study_participant_id': study_participant_id,
                        'study_id': study_id,
                        'study_step_id': step_id,
                        'context_tag': context_tag,
                    }
                )
            )
            if existing_ctx:
                result = ResponseWrapper.model_validate(existing_ctx.recommendations_json)
                return await self._process_recommendation_result(result)

        participant = await self.study_participant_repository.find_one(
            RepoQueryOptions(
                ids=[study_participant_id], load_options=StudyParticipantRepository.LOAD_ASSIGNED_CONDITION
            )
        )
        if not participant or not participant.study_condition:
            raise ValueError('Participant or Condition not found')

        algorithm_key = participant.study_condition.recommender_key
        limit = participant.study_condition.recommendation_count

        strategy = REGISTRY.get(algorithm_key)
        if not strategy:
            raise ValueError(f'No strategy found for key: {algorithm_key}')

        ratings_models = await self.participant_rating_repository.find_many(
            RepoQueryOptions(filters={'study_participant_id': study_participant_id})
        )
        movies = await self.movie_repository.find_many(RepoQueryOptions(ids=[r.item_id for r in ratings_models]))
        movie_map = {m.id: m.movielens_id for m in movies}

        ratings = []
        for r in ratings_models:
            if r.item_id in movie_map:
                ratings.append(MovieLensRating(item_id=movie_map[r.item_id], rating=r.rating))
            else:
                log.warning(f'Rating for item {r.item_id} skipped: Movie not found in DB')

        try:
            # Record Interaction (Side Effect)
            if context_data and context_data.get('emotion_input'):
                try:
                    step_id_str = context_data.get('step_id')
                    if step_id_str:
                        step_id = uuid.UUID(str(step_id_str))
                        context_tag = 'emotion_tuning'

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
                                study_id=participant.study_id,
                                study_participant_id=participant.id,
                                study_step_id=step_id,
                                context_tag=context_tag,
                                payload_json=DynamicPayload(extra={'history': [new_entry]}),
                            )
                            await self.participant_interaction_repository.create(payload)

                except Exception as e:
                    log.error(f'Failed to record interaction: {e}')

            result = await strategy.recommend(
                user_id=str(study_participant_id), ratings=ratings, limit=limit, run_config=context_data
            )
            log.info(f'Result in recommender_service.py (Line 231): {result}')

            rec_ctx = ParticipantRecommendationContext(
                study_id=study_id,
                study_step_id=step_id,
                study_step_page_id=step_page_id,  # Might be None, schema allows it
                study_participant_id=study_participant_id,  # Correct field name for Model
                context_tag=context_tag,
                recommendations_json=result.model_dump(),
            )
            await self.recommendation_context_repository.create(rec_ctx)
            return await self._process_recommendation_result(result)
        except Exception as e:
            log.error(f'Error for {study_participant_id} [{algorithm_key}]: {e}')
            raise

    async def _process_recommendation_result(self, result: ResponseWrapper) -> RecommendationResponse:
        if result.response_type == 'standard':
            return await self._enrich_with_moviedata([cast(str, rec_item) for rec_item in result.items])

        if result.response_type == 'community_advisors':
            return await self._enrich_advisor_response(result)

        if result.response_type == 'community_scores':
            return await self._enrich_pref_viz_response(result)

        raise KeyError('Result response_type key did not match any known types.')

    async def _enrich_advisor_response(self, response: ResponseWrapper) -> RecommendationResponse:
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

    async def _enrich_pref_viz_response(self, response: ResponseWrapper) -> RecommendationResponse:
        all_rec_ids = set()
        comm_scores = []
        for score_item in response.items:
            score_item = cast(CommunityScoreRecItem, score_item)
            comm_scores.append(score_item)
            all_rec_ids.add(score_item.item_id)

        movies = await self._enrich_with_moviedata(list(all_rec_ids))
        movies_dict = {int(m.movielens_id): m for m in movies}
        return {
            score_item.item_id: EnrichedCommunityScoreItem(
                item=movies_dict[int(score_item.item_id)], **score_item.model_dump(exclude={'item_id'})
            )
            for score_item in comm_scores
        }

    async def _enrich_with_moviedata(self, movielens_ids: list[str]) -> list[MovieDetailSchema]:
        options = RepoQueryOptions(filters={'movielens_id': movielens_ids}, load_options=MovieRepository.LOAD_ALL)
        movies = await self.movie_repository.find_many(options)

        return [MovieDetailSchema.model_validate(movie) for movie in movies]
