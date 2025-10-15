import uuid
from random import shuffle
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from data.schemas.movie_schemas import MovieSchema
from data.schemas.participant_response_schemas import MovieLensRatingSchema, RatedItemBaseSchema
from data.schemas.preferences_schemas import (
    AdvisorProfileSchema,
    Avatar,
)
from data.services import MovieService
from data.services.content_dependencies import get_movie_service as movie_service
from docs.metadata import RSTagsEnum as Tags
from services.recommenders.alt_rec_service import AlternateRS
from services.recommenders.pref_com_service import PreferenceCommunity
from services.recommenders.service_manager import get_altrec_service, get_prefcom_service

router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)
CACHE_LIMIT = 100
queue = []
CACHE = {}


class AdvisorIDSchema(BaseModel):
    advisor_id: int


class RecommendationRequestPayload(BaseModel):
    context_tag: str
    ratings: list[RatedItemBaseSchema]


CONDITIONS_MAP = {'topN': 0, 'controversial': 1, 'hate': 2, 'hip': 3, 'noclue': 4}

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
    movie_service: Annotated[MovieService, Depends(movie_service)],
    rssa_pref_comm: Annotated[PreferenceCommunity, Depends(get_prefcom_service)],
):
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
    return advisors


@router.post('/altrecs', response_model=list[MovieSchema])
async def get_alt_recs(
    payload: RecommendationRequestPayload,
    movie_service: Annotated[MovieService, Depends(movie_service)],
    rssa_alt_recs: Annotated[AlternateRS, Depends(get_altrec_service)],
):
    print('HELLOW', payload)
    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]
    recs = rssa_alt_recs.get_condition_prediction(
        ratings_with_movielens_ids, 'xyz', int(CONDITIONS_MAP[payload.context_tag]), 10
    )
    movies = await movie_service.get_movies_by_movielens_ids([str(rec) for rec in recs])
    print('BYE', recs, movies)
    return [MovieSchema.model_validate(movie) for movie in movies]
