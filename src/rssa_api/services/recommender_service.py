import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import joinedload
from rssa_api.data.models.study_participants import StudyParticipant, ParticipantRecommendationContext
from rssa_api.data.repositories.base_repo import RepoQueryOptions
from rssa_api.data.repositories.items.movies import MovieRepository
from rssa_api.data.repositories.participant_responses import (
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
)
from rssa_api.data.repositories.study_participants.study_participants import StudyParticipantRepository
from rssa_api.data.repositories.study_participants.recommendation_context import (
    ParticipantRecommendationContextRepository,
)
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
from rssa_api.data.utility import convert_datetime_to_str, convert_uuids_to_str



from .recommendation.registry import REGISTRY
from random import shuffle

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
        self, study_id: uuid.UUID, study_participant_id: uuid.UUID, context_data: dict = None
    ) -> RecommendationResponse:
        # 0. Check for existing Recommendation Context (Persistence)
        # ------------------------------------------------------------
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

        if step_id and context_tag:
             existing_ctx = await self.recommendation_context_repository.find_one(
                RepoQueryOptions(
                    fields=[
                        ('study_participant_id', study_participant_id),
                        ('study_id', study_id),
                        ('step_id', step_id),
                        ('context_tag', context_tag)
                    ]
                )
            )
             if existing_ctx:
                 log.info(f"Returning stored recommendations for participant {study_participant_id} step {step_id}")
                 cached_data = existing_ctx.recommendations_json
                 
                 # Attempt to reconstruct appropriate response type
                 if isinstance(cached_data, dict):
                     # Check if it looks like EnrichedRecResponse
                     if 'recommendations' in cached_data and 'total_count' in cached_data and isinstance(cached_data['recommendations'], list):
                          # Re-validate with schema to get Pydantic objects back if needed, or return dict if allowed
                          # The return type annotation says RecommendationResponse which includes EnrichedRecResponse (Pydantic model)
                          try:
                              return EnrichedRecResponse(**cached_data)
                          except Exception as e:
                              log.warning(f"Failed to reconstruct EnrichedRecResponse from cache: {e}")
                              return cached_data
                     
                     # Check if it is Advisors (dict of objects) - The schemas expect dict[str, AdvisorProfileSchema] in some router endpoints
                     # But here we return a dict. If the router expects Pydantic models, we might need to cast.
                     # However, FastApi response_model usually handles dict->Model conversion if structure matches.
                     return cached_data
            
        # 1. Fetch User & Strategy
        participant = await self.study_participant_repository.find_one(
            RepoQueryOptions(
                ids=[study_participant_id], load_options=[joinedload(StudyParticipant.study_condition)]
            )
        )
        if not participant or not participant.study_condition:
            raise ValueError('Participant or Condition not found')

        algorithm_key = participant.study_condition.recommender_key
        limit = participant.study_condition.recommendation_count
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

            # Returns a polymorphic RecommendationResponse (Standard OR Insight OR Advisor)
            result = await strategy.recommend(
                user_id=study_participant_id, ratings=ratings, limit=limit, run_config=context_data
            )

            # Polymorphic Enrichment
            final_response = None

            # CASE A: Standard List of Items (Top-N, Diverse-N)
            if isinstance(result, StandardRecResponse):
                final_response = await self._enrich_standard_response(result)

            # CASE B: Community Insight (Scatter plots, etc.)
            elif hasattr(result, 'response_type') and result.response_type == 'community_comparison':
                final_response = result

            # CASE C: Advisor Recommendations
            elif hasattr(result, 'advisors'):
                final_response = await self._enrich_advisor_response(result)

            # CASE D: Other types
            else:
                final_response = result

            # 4. Persistence (Store generated context)
            if step_id and context_tag and final_response:
                try:
                    # Serialize response for storage
                    to_store = final_response
                    if hasattr(final_response, 'model_dump'):
                         to_store = final_response.model_dump()
                    elif isinstance(final_response, dict):
                         # If it's a dict of Pydantic models (like Advisors), dump them
                         # Check strictness based on known structure?
                         # Assume generic dict serialization
                         # For now, generic convert util handles UUIDs/DateTimes, but Pydantic models inside dict need manual dump
                         # Advisor response is dict[str, AdvisorProfileSchema] -> need to dump values
                         to_store = {}
                         for k, v in final_response.items():
                              if hasattr(v, 'model_dump'):
                                   to_store[k] = v.model_dump()
                              else:
                                   to_store[k] = v
                    
                    json_safe_dict = convert_uuids_to_str(to_store)
                    json_safe_dict = convert_datetime_to_str(json_safe_dict)

                    rec_ctx = ParticipantRecommendationContext(
                        study_id=study_id,
                        step_id=step_id,
                        step_page_id=step_page_id, # Might be None, schema allows it
                        study_participant_id=study_participant_id, # Correct field name for Model
                        context_tag=context_tag,
                        recommendations_json=json_safe_dict,
                    )
                    await self.recommendation_context_repository.create(rec_ctx)
                    log.info(f"Stored recommendations for {study_participant_id} step {step_id}")
                except Exception as e:
                    log.error(f"Failed to store recommendation context: {e}")

            return final_response

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

    async def _enrich_advisor_response(self, response):
        """Helper to hydrate Advisor responses with movie data"""
        
        # 1. Collect all Movie IDs
        # response.advisors is expected to be a dict based on logs, or object with attributes if coming from new Strategy class
        # But 'result.advisors' from new strategy is the raw dict from body['advisors']
        
        raw_advisors = response.advisors
        # It is a dict: { "id": { "id": ..., "recommendation": ..., "profile_top_n": ... } }
        
        all_movie_ids = set()
        
        advisor_values = raw_advisors.values() if isinstance(raw_advisors, dict) else raw_advisors

        for advisor in advisor_values:
            # Handle dict access vs object access safety
            if isinstance(advisor, dict):
                 rec_id = advisor.get('recommendation')
                 movies = advisor.get('profile_top_n')
            else:
                 rec_id = getattr(advisor, 'recommendation', None)
                 movies = getattr(advisor, 'profile_top_n', getattr(advisor, 'movies', None))

            if rec_id:
                all_movie_ids.add(str(rec_id))
            
            if movies:
                for mid in movies:
                    all_movie_ids.add(str(mid))
        
        if not all_movie_ids:
             return raw_advisors # Fallback

        # 2. Fetch all Movies
        movies_db = await self.movie_repository.find_many(
            RepoQueryOptions(
                filters={'movielens_id': list(all_movie_ids)},
                load_options=[joinedload(Movie.emotions), joinedload(Movie.recommendations_text)]
            )
        )
        movie_map = {m.movielens_id: m for m in movies_db}

        # 3. Avatars
        avatar_pool = list(AVATARS.keys())
        shuffle(avatar_pool)

        # 4. Reconstruct Advisors with hydrated data
        from rssa_api.data.schemas.preferences_schemas import AdvisorProfileSchema, Avatar

        enriched_advisors = {}
        for advisor in advisor_values:
            # Normalize access
            if isinstance(advisor, dict):
                 adv_id = advisor.get('id')
                 rec_id = advisor.get('recommendation')
                 movies_ids = advisor.get('profile_top_n')
                 existing_avatar = advisor.get('avatar')
            else:
                 adv_id = getattr(advisor, 'id')
                 rec_id = getattr(advisor, 'recommendation', None)
                 movies_ids = getattr(advisor, 'profile_top_n', getattr(advisor, 'movies', None))
                 existing_avatar = getattr(advisor, 'avatar', None)

            # Hydrate Recommendation
            rec_id_str = str(rec_id)
            rec_obj = None
            if rec_id_str in movie_map:
                rec_obj = MovieDetailSchema.model_validate(movie_map[rec_id_str])
            
            # Hydrate Movie List
            movies_list_obj = []
            if movies_ids:
                for mid in movies_ids:
                    mid_str = str(mid)
                    if mid_str in movie_map:
                        movies_list_obj.append(MovieSchema.model_validate(movie_map[mid_str]))
            
            # Avatar
            # Pick valid random avatar if none exists (reusing pool logic)
            final_avatar = None
            if existing_avatar:
                 final_avatar = existing_avatar
            elif len(avatar_pool) > 0:
                 key = avatar_pool.pop()
                 final_avatar = Avatar.model_validate(AVATARS[key])
            else:
                 # Fallback if pool exhausted (unlikely with 7 advisors and plenty avatars)
                 final_avatar = Avatar(name="Anonymous", alt="Anonymous Advisor", src="cow")

            # Create new AdvisorProfileSchema
            if rec_obj:
                new_advisor = AdvisorProfileSchema(
                    id=str(adv_id),
                    recommendation=rec_obj, # Now a full object
                    movies=movies_list_obj, # Now full objects
                    avatar=final_avatar
                )
                enriched_advisors[str(adv_id)] = new_advisor
            else:
                log.warning(f"Advisor {adv_id} skipped: Recommendation movie {rec_id} not found")

        # 4. Return new structure (preserving any metadata if response has it)
        # We return the dict to match frontend expectations
        
        return enriched_advisors
