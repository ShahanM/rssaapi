import uuid
from random import shuffle
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from rssa_api.auth.authorization import get_current_participant, validate_api_key
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.schemas.movie_schemas import MovieSchema
from rssa_api.data.schemas.participant_response_schemas import MovieLensRatingSchema, RatedItemBaseSchema
from rssa_api.data.schemas.preferences_schemas import (
    AdvisorProfileSchema,
    Avatar,
    RecommendationContextBaseSchema,
    RecommendationJsonPrefCommSchema,
    RecommendationRequestPayload,
)
from rssa_api.data.services import MovieServiceDep, StudyConditionServiceDep, StudyParticipantServiceDep
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.services.recommenders.pref_com_service import PreferenceCommunity

IMPLICIT_MODEL_PATH = 'implicit_als_ml32m'
router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)
CACHE_LIMIT = 100
queue = []
CACHE = {}


class AdvisorIDSchema(BaseModel):
    advisor_id: int


class TempRequestSchema(BaseModel):
    ratings: list[RatedItemBaseSchema]
    rec_type: Literal['baseline', 'reference', 'diverse']


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


@router.post('/prefcomm', response_model=dict[str, AdvisorProfileSchema])
async def get_advisor(
    payload: RecommendationRequestPayload,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
    movie_service: MovieServiceDep,
    condition_service: StudyConditionServiceDep,
    participant_service: StudyParticipantServiceDep,
):
    rec_ctx = await participant_service.get_recommndation_context_by_participant_context(
        study_id, participant.id, payload.context_tag
    )

    if rec_ctx:
        return {adv.id: adv for adv in rec_ctx.recommendations_json.advisors}

    condition = await condition_service.get_study_condition(participant.condition_id)

    # rssa_itm_pop, rssa_ave_scores = get_rssa_ers_data()
    # rssa_model_path = get_rssa_model_path()
    # rssa_pref_comm = PreferenceCommunity(rssa_model_path, rssa_itm_pop, rssa_ave_scores, get_rating_data_path())

    rssa_pref_comm = PreferenceCommunity(IMPLICIT_MODEL_PATH)

    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]

    recs = rssa_pref_comm.get_advisors_with_profile(ratings_with_movielens_ids, num_rec=7)

    avatar_pool = list(AVATARS.keys())
    shuffle(avatar_pool)
    advisors = {}
    for adv, value in recs.items():
        profile_movies = await movie_service.get_movies_by_movielens_ids([str(val) for val in value['profile_top']])
        recommendation = await movie_service.get_movie_details_by_movielens_id(str(value['recommendation']))

        validated_movies = [MovieSchema.model_validate(m) for m in profile_movies]
        avatar = Avatar.model_validate(AVATARS[avatar_pool.pop()])

        advprofile = AdvisorProfileSchema(
            id=str(adv), movies=validated_movies, recommendation=recommendation, avatar=avatar
        )
        advisors[str(adv)] = advprofile
    rec_ctx_create_req = RecommendationContextBaseSchema(
        step_id=payload.step_id,
        step_page_id=payload.step_page_id,
        context_tag=payload.context_tag,
        recommendations_json=RecommendationJsonPrefCommSchema(condition=condition, advisors=list(advisors.values())),
    )
    recommendation_context = await participant_service.create_recommendation_context(
        study_id, participant.id, rec_ctx_create_req
    )

    return advisors
