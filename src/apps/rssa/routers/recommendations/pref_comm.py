import uuid
from random import random, shuffle
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.authorization import get_current_participant, validate_api_key
from compute.rspc import PreferenceCommunity
from compute.utils import get_rating_data_path, get_rssa_ers_data, get_rssa_model_path
from data.models.study_participants import StudyParticipant
from data.schemas.movie_schemas import MovieDetailSchema, MovieSchema
from data.schemas.participant_response_schemas import MovieLensRatingSchema, RatedItemBaseSchema
from data.services import MovieService, StudyConditionService
from data.services.content_dependencies import get_movie_service as movie_service
from data.services.rssa_dependencies import get_study_condition_service as study_condition_service
from docs.metadata import RSTagsEnum as Tags

router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)
CACHE_LIMIT = 100
queue = []
CACHE = {}


class AdvisorIDSchema(BaseModel):
    advisor_id: int


# class MovieRecommedantion(MovieSchema, MovieRecommendationSchema):
# pass


class TempRequestSchema(BaseModel):
    ratings: list[RatedItemBaseSchema]
    rec_type: Literal['baseline', 'reference', 'diverse']


class Avatar(BaseModel):
    name: str
    alt: str
    src: str


class AdvisorProfileSchema(BaseModel):
    id: str
    movies: List[MovieSchema]
    recommendation: MovieDetailSchema
    avatar: Optional[Avatar]


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
    payload: TempRequestSchema,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
    movie_service: Annotated[MovieService, Depends(movie_service)],
    condition_service: Annotated[StudyConditionService, Depends(study_condition_service)],
):
    sorted_ratings = sorted(payload.ratings, key=lambda x: x.item_id)
    condition = await condition_service.get_study_condition(participant.condition_id)
    cache_key = (
        participant.id,
        tuple(sorted_ratings),
        participant.condition_id,
        study_id,
    )
    if cache_key in CACHE:
        print('Found request in cache. Returning cached response.')
        return CACHE[cache_key]

    rssa_itm_pop, rssa_ave_scores = get_rssa_ers_data()
    rssa_model_path = get_rssa_model_path()
    rssa_pref_comm = PreferenceCommunity(rssa_model_path, rssa_itm_pop, rssa_ave_scores, get_rating_data_path())

    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]

    recs = rssa_pref_comm.get_advisors_with_profile(ratings_with_movielens_ids, str(participant.id), num_rec=7)

    avatar_pool = list(AVATARS.keys())
    shuffle(avatar_pool)
    advisors = {}
    for adv, value in recs.items():
        profile_movies = await movie_service.get_movies_by_movielens_ids([str(val) for val in value['profile_top']])
        recommendation = await movie_service.get_movie_details_by_movielens_id(str(value['recommendation']))
        # recommendation = recommendation[0]

        # rec_details = await get_movie_recommendation_text(db, recommendation.id)

        # if rec_details is not None:
        # 	movie_rec_dict = recommendation.model_dump()
        # 	movie_rec_dict.update(rec_details.model_dump())
        # 	movie_rec = MovieRecommedantion(**movie_rec_dict)

        # advprofile = AdvisorProfileSchema(id=str(adv), movies=profile_movies, recommendation=movie_rec)
        validated_movies = [MovieSchema.model_validate(m) for m in profile_movies]
        # validated_rec = MovieDetailSchema.model_validate(recommendation)
        avatar = Avatar.model_validate(AVATARS[avatar_pool.pop()])

        advprofile = AdvisorProfileSchema(
            id=str(adv), movies=validated_movies, recommendation=recommendation, avatar=avatar
        )
        advisors[str(adv)] = advprofile

    if len(queue) >= CACHE_LIMIT:
        old_key = queue.pop(0)
        del CACHE[old_key]
    CACHE[cache_key] = advisors
    queue.append(cache_key)

    return advisors
