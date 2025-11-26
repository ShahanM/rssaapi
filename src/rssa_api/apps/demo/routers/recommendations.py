from random import shuffle
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from rssa_api.data.schemas.movie_schemas import MovieSchema
from rssa_api.data.schemas.participant_response_schemas import MovieLensRatingSchema, RatedItemBaseSchema
from rssa_api.data.schemas.preferences_schemas import (
    AdvisorProfileSchema,
    Avatar,
)
from rssa_api.data.services import MovieServiceDep
from rssa_api.data.services.content_dependencies import get_movie_service as movie_service
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.services.recommenders.alt_rec_service import AlternateRS
from rssa_api.services.recommenders.emotions_rs_service import EmotionsRS
from rssa_api.services.recommenders.pref_com_service import PreferenceCommunity

IMPLICIT_MODEL_PATH = 'implicit_als_ml32m'
EMOTIONS_MODEL_PATH = 'implicit_als_ers_ml32m'
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
    movie_service: MovieServiceDep,
):
    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]
    rssa_pref_comm = PreferenceCommunity(IMPLICIT_MODEL_PATH)
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
    movie_service: MovieServiceDep,
):
    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]
    rssa_alt_recs = AlternateRS(IMPLICIT_MODEL_PATH)
    recs = rssa_alt_recs.get_condition_prediction(
        ratings_with_movielens_ids, 'xyz', int(CONDITIONS_MAP[payload.context_tag]), 10
    )
    movies = await movie_service.get_movies_by_movielens_ids([str(rec) for rec in recs])
    return [MovieSchema.model_validate(movie) for movie in movies]


# SCORER_FUNCTION_URL = 'https://2rbap5audc.execute-api.us-east-1.amazonaws.com/default/recommender-scorer'

ALT_RECS_FUNC_URL = 'https://9mtnkol2ne.execute-api.us-east-1.amazonaws.com/alt-recs/predict_top_n'


class RecommendationRequest(BaseModel):
    user_id: str
    ratings: list[MovieLensRatingSchema]
    n: int


@router.post('/altrecs/function', response_model=Any)
async def get_alt_rec_do_func(
    payload: RecommendationRequestPayload,
    movie_service: MovieServiceDep,
):
    """
    This endpoint takes a user and their ratings, sends them to the
    DigitalOcean 'scorer' function, and returns the recommendations.
    You can specify which model to use via the 'model_prefix' field.
    """
    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]
    if not ALT_RECS_FUNC_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Scorer function URL is not configured.'
        )

    request_payload = RecommendationRequest(user_id='123', ratings=ratings_with_movielens_ids, n=200).model_dump(
        exclude_none=True
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(ALT_RECS_FUNC_URL, json=request_payload)
            print('This is the reponse', response)
            response.raise_for_status()

            result = response.json()
            print(result)
            # if result.get('statusCode', 500) >= 400:
            #     error_detail = result.get('body', {}).get('error', 'Uknown function error')
            #     raise HTTPException(
            #         status_code=status.HTTP_502_BAD_GATEWAY, detail=f'Recommedantion service failed: {error_detail}'
            #     )
            scored_ids = result.get('body')
            # return scored_ids
            return result
        except httpx.ReadError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'Error while requesting recommendation service: {exc}',
            ) from exc
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'An internal lerror occured: {e}'
            ) from e


@router.post('/iers', response_model=list[MovieSchema])
async def get_iers_recommendations(
    payload: RecommendationRequestPayload,
    movie_service: MovieServiceDep,
):
    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]

    ers_recs_service = EmotionsRS(EMOTIONS_MODEL_PATH)


# @router.put('/experimental/recommendations/', response_model=List[ERSMovieSchema])
# async def update_recommendations_experimental(
#     rated_movies: EmotionInputSchemaExperimental, db: Session = Depends(movie_db)
# ):
#     iers_item_pop, iersg20 = get_iers_data()
#     iers_model_path = get_iers_model_path()
#     iersalgs = EmotionsRS(iers_model_path, iers_item_pop, iersg20)
#     recs = []
#     if rated_movies.input_type == 'discrete':
#         emo_in = [EmotionDiscreteInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
#         if rated_movies.condition_algo == 1:
#             recs = iersalgs.predict_discrete_tuned_topN(
#                 ratings=rated_movies.ratings,
#                 user_id=str(rated_movies.user_id),
#                 emotion_input=emo_in,
#                 num_rec=rated_movies.num_rec,
#                 item_pool_size=rated_movies.item_pool_size,
#                 scale_vector=rated_movies.scale_vector,
#                 lowval=rated_movies.low_val,
#                 highval=rated_movies.high_val,
#                 ranking_strategy=rated_movies.algo,
#                 dist_method=rated_movies.dist_method,
#             )
#         elif rated_movies.condition_algo == 2:
#             div_sample_size = rated_movies.diversity_sample_size
#             assert div_sample_size is not None
#             recs = iersalgs.predict_discrete_tuned_diverseN(
#                 ratings=rated_movies.ratings,
#                 user_id=str(rated_movies.user_id),
#                 emotion_input=emo_in,
#                 num_rec=rated_movies.num_rec,
#                 sampling_size=div_sample_size,
#                 item_pool_size=rated_movies.item_pool_size,
#                 scale_vector=rated_movies.scale_vector,
#                 lowval=rated_movies.low_val,
#                 highval=rated_movies.high_val,
#                 ranking_strategy=rated_movies.algo,
#                 div_crit=rated_movies.diversity_criterion,
#                 dist_method=rated_movies.dist_method,
#             )

#     elif rated_movies.input_type == 'continuous':
#         # Not implemented yet
#         emo_in = [EmotionContinuousInputSchema(**emoin.dict()) for emoin in rated_movies.emotion_input]
#         if rated_movies.condition_algo == 1:
#             recs = iersalgs.predict_continuous_tuned_topN(
#                 ratings=rated_movies.ratings,
#                 user_id=rated_movies.user_id,
#                 emotion_input=emo_in,
#                 num_rec=rated_movies.num_rec,
#                 scale_vector=rated_movies.scale_vector,
#                 algo=rated_movies.algo,
#                 dist_method=rated_movies.dist_method,
#                 item_pool_size=rated_movies.item_pool_size,
#             )

#     recs = [str(rec) for rec in recs if rec is not None]
#     if len(recs) == 0:
#         raise HTTPException(status_code=406, detail='User condition not found')

#     movies = get_ers_movies_by_movielens_ids(db, recs)

#     return movies
