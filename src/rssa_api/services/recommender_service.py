import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import joinedload
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.models.movies import Movie
from rssa_api.data.repositories.base_repo import RepoQueryOptions
from rssa_api.data.repositories.items.movies import MovieRepository
from rssa_api.data.repositories.participant_responses import (
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
)
from rssa_api.data.repositories.study_participants.study_participants import StudyParticipantRepository
from rssa_api.data.schemas.movie_schemas import MovieSchema, MovieDetailSchema
from rssa_api.data.schemas.participant_response_schemas import (
    MovieLensRating,
    ParticipantStudyInteractionResponseCreate,
    DynamicPayload,
)
from rssa_api.data.schemas.recommendations import (
    EnrichedRecResponse,
    RecommendationResponse,
    StandardRecResponse,
)

from .recommendation.registry import REGISTRY

log = logging.getLogger(__name__)


class RecommenderService:
    def __init__(
        self,
        study_participant_repository: StudyParticipantRepository,
        participant_rating_repository: ParticipantRatingRepository,
        movie_repository: MovieRepository,
        participant_interaction_repository: ParticipantStudyInteractionResponseRepository,
    ):
        self.study_participant_repository = study_participant_repository
        self.participant_rating_repository = participant_rating_repository
        self.movie_repository = movie_repository
        self.participant_interaction_repository = participant_interaction_repository

    async def get_recommendations(
        self, study_participant_id: uuid.UUID, limit: int = 10, context_data: dict = None
    ) -> RecommendationResponse:
        # Fetch User & Strategy
        participant = await self.study_participant_repository.find_one(
            RepoQueryOptions(
                ids=[study_participant_id], load_options=[joinedload(StudyParticipant.study_condition)]
            )
        )
        if not participant or not participant.study_condition:
            raise ValueError('Participant or Condition not found')

        algorithm_key = participant.study_condition.recommender_key
        strategy = REGISTRY.get(algorithm_key)
        if not strategy:
            raise ValueError(f'No strategy found for key: {algorithm_key}')

        # Fetch History
        ratings_models = await self.participant_rating_repository.find_many(
            RepoQueryOptions(filters={'study_participant_id': study_participant_id})
        )
        movies = await self.movie_repository.find_many(
            RepoQueryOptions(ids=[r.item_id for r in ratings_models])
        )
        movie_map = {m.id: m.movielens_id for m in movies}
        
        # Safely map ratings, skipping any that don't have a corresponding movie in DB
        ratings = []
        for r in ratings_models:
            if r.item_id in movie_map:
                ratings.append(MovieLensRating(item_id=movie_map[r.item_id], rating=r.rating))
            else:
                log.warning(f"Rating for item {r.item_id} skipped: Movie not found in DB")

        # Execute Strategy
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
                                    'study_step_id': step_id
                                }
                            )
                        )
                        
                        new_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'emotion_input': context_data['emotion_input']
                        }

                        if existing_interaction:
                            # Update existing
                            current_payload = existing_interaction.payload_json
                            history = current_payload.get('history', [])
                            if not isinstance(history, list):
                                history = []
                            history.append(new_entry)
                            
                            # Update
                            updated_payload = {**current_payload, 'history': history}
                            await self.participant_interaction_repository.update(
                                existing_interaction.id,
                                {'payload_json': updated_payload}
                            )
                        else:
                            # Create new
                            payload = ParticipantStudyInteractionResponseCreate(
                                study_id=participant.study_id,
                                study_participant_id=participant.id,
                                study_step_id=step_id,
                                context_tag=context_tag,
                                payload_json=DynamicPayload(extra={'history': [new_entry]})
                            )
                            await self.participant_interaction_repository.create(payload)
                            
                except Exception as e:
                    log.error(f"Failed to record interaction: {e}")

            # Returns a polymorphic RecommendationResponse (Standard OR Insight)
            result = await strategy.recommend(
                user_id=study_participant_id, ratings=ratings, limit=limit, run_config=context_data
            )

            # Polymorphic Enrichment

            # CASE A: Standard List of Items (Top-N, Diverse-N)
            if isinstance(result, StandardRecResponse):
                return await self._enrich_standard_response(result)

            # CASE B: Community Insight (Scatter plots, etc.)
            elif hasattr(result, 'response_type') and result.response_type == 'community_comparison':
                return result

            # CASE C: Other types (If needed)
            return result

        except Exception as e:
            log.error(f'Error for {study_participant_id} [{algorithm_key}]: {e}')
            raise

    async def _enrich_standard_response(self, response: StandardRecResponse) -> EnrichedRecResponse:
        """Helper to fetch Movie Metadata for a list of IDs"""
        if not response.items:
            return EnrichedRecResponse(recommendations=[], total_count=0)

        # Extract IDs assuming recommendations are simple list of ints (from StandardRecResponse)
        item_ids = [str(r) for r in response.items]
        log.info(f"Enriching IDs: {item_ids}")

        movies_db = await self.movie_repository.find_many(
            RepoQueryOptions(
                filters={'movielens_id': item_ids},
                load_options=[joinedload(Movie.emotions), joinedload(Movie.recommendations_text)]
            )
        )
        log.info(f"Found {len(movies_db)} movies in DB matching IDs")
        
        movie_map = {m.movielens_id: m for m in movies_db}

        enriched_list = []
        for item_id_int in response.items:
            mid = str(item_id_int)
            if mid in movie_map:
                movie_obj = MovieDetailSchema.model_validate(movie_map[mid])
                enriched_list.append(movie_obj)
            else:
                 log.warning(f"Movie ID {mid} from strategy not found in DB")

        log.info(f"Final Enriched List Size: {len(enriched_list)}")

        # Return a new response with full movie objects
        return EnrichedRecResponse(recommendations=enriched_list, total_count=len(enriched_list))
