import uuid
from typing import Annotated, Union

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import get_current_participant, validate_api_key
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.schemas.movie_schemas import MovieDetailSchema
from rssa_api.data.schemas.participant_response_schemas import MovieLensRatingSchema
from rssa_api.data.schemas.preferences_schemas import (
    EmotionContinuousInputSchema,
    EmotionDiscreteInputSchema,
    RecommendationRequestPayload,
)
from rssa_api.data.services import MovieService, ParticipantService, StudyConditionService
from rssa_api.data.services.content_dependencies import get_movie_service as movie_service
from rssa_api.data.services.rssa_dependencies import (
    get_participant_service as participant_service,
)
from rssa_api.data.services.rssa_dependencies import (
    get_study_condition_service as study_condition_service,
)
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.services.recommenders.emotions_rs_service import EmotionsRS

EMOTIONS_MODEL_PATH = 'implicit_als_ers_ml32m'
router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)
# TODO: Move to config file
TOP_N_TUNING_PARAMS = {
    'item_pool_size': 200,
    'scale_vector': False,  # scale vector only applicable for distance strategy
    'low_val': -0.125,
    'high_val': 0.125,
    'ranking_strategy': 'weighted',
    'distance_method': 'sqrtcityblock',  # only applicable for distance strategy
}

# TODO: Move to config file
DIVERSE_N_TUNING_PARAMS = {
    'item_pool_size': 200,
    'scale_vector': False,  # scale vector only applicable for distance strategy
    'diversity_sample_size': 100,
    'low_val': -0.125,
    'high_val': 0.125,
    'ranking_strategy': 'weighted',
    'diversity_criteria': 'unspecified',
    'distance_method': 'sqrtcityblock',  # only applicable for distance strategy
}


@router.post('/ers', response_model=list[MovieDetailSchema])
async def generation_emotions_recommendation(
    payload: RecommendationRequestPayload,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
    movie_service: Annotated[MovieService, Depends(movie_service)],
    condition_service: Annotated[StudyConditionService, Depends(study_condition_service)],
    participant_service: Annotated[ParticipantService, Depends(participant_service)],
):
    """Generate recommendationtions for the emotions recommender system study.

    Args:
        rated_movies: _description_

    Returna:
        list
    """
    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]

    ers_recs_service = EmotionsRS(EMOTIONS_MODEL_PATH)

    condition = await condition_service.get_study_condition(participant.condition_id)
    # recs: List[int] = []
    # user_condition = 5
    # ratins = {rat.item_id: rat.rating for rat in user_ratings.ratings}
    # movies = await movie_service.get_movies_from_ids(list(ratins.keys()))
    # movies = get_ers_movies_by_ids_v2(db, list(ratins.keys()))
    # newratins = [RatedItemSchema(item_id=int(m.movielens_id), rating=ratins[m.id]) for m in movies]
    recs = []
    if condition in [1, 2, 3, 4]:
        recs = ers_recs_service.predict_topN(
            str(participant.id),
            ratings_with_movielens_ids,
            condition.recommendation_count,
        )
    elif condition in [5, 6, 7, 8]:
        recs = ers_recs_service.predict_diverseN(
            str(participant.id),
            ratings_with_movielens_ids,
            condition.recommendation_count,
            item_pool_size=DIVERSE_N_TUNING_PARAMS['item_pool_size'],
            sampling_size=DIVERSE_N_TUNING_PARAMS['diversity_sample_size'],
        )
    recs = [str(rec) for rec in recs if rec is not None]
    if len(recs) == 0:
        raise HTTPException(status_code=406, detail='User condition not found')
    movies = await movie_service.get_movies_with_emotions_by_movielens_ids(recs)

    return movies


ERSControlType = Union[EmotionDiscreteInputSchema, EmotionContinuousInputSchema]


class ERSUpdateRequestPayload(RecommendationRequestPayload):
    emotion_input: list[ERSControlType]


@router.post('/ers/update', response_model=list[MovieDetailSchema])
async def update_recommendations(
    payload: ERSUpdateRequestPayload,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
    movie_service: Annotated[MovieService, Depends(movie_service)],
    condition_service: Annotated[StudyConditionService, Depends(study_condition_service)],
    participant_service: Annotated[ParticipantService, Depends(participant_service)],
):
    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]

    ers_recs_service = EmotionsRS(EMOTIONS_MODEL_PATH)

    condition = await condition_service.get_study_condition(participant.condition_id)
    if condition is None:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED, detail='Something is not right with the participant data.'
        )
    # ratins = {rat.item_id: rat.rating for rat in rated_movies.ratings}
    # movies = get_ers_movies_by_ids_v2(db, list(ratins.keys()))
    # newratins = [RatedItemSchema(item_id=int(m.movielens_id), rating=ratins[m.id]) for m in movies]
    ers_control_input = payload.emotion_input
    recs = []
    # FIXME the frontend should call the correct endpoint based on the condition. Current method is not RESTful.
    if isinstance(ers_control_input[0], EmotionDiscreteInputSchema):
        emo_in = [EmotionDiscreteInputSchema.model_validate(emoin) for emoin in ers_control_input]
        if condition in [1, 2, 3, 4]:
            recs = ers_recs_service.predict_discrete_tuned_topN(
                user_id=str(participant.id),
                ratings=ratings_with_movielens_ids,
                emotion_input=emo_in,
                num_rec=condition.recommendation_count,
                item_pool_size=TOP_N_TUNING_PARAMS['item_pool_size'],
                scale_vector=TOP_N_TUNING_PARAMS['scale_vector'],
                lowval=TOP_N_TUNING_PARAMS['low_val'],
                highval=TOP_N_TUNING_PARAMS['high_val'],
                ranking_strategy=TOP_N_TUNING_PARAMS['ranking_strategy'],
                dist_method=TOP_N_TUNING_PARAMS['distance_method'],
            )
        elif condition in [5, 6, 7, 8]:
            div_sample_size = DIVERSE_N_TUNING_PARAMS['diversity_sample_size']
            assert div_sample_size is not None
            recs = ers_recs_service.predict_discrete_tuned_diverseN(
                user_id=str(participant.id),
                ratings=ratings_with_movielens_ids,
                emotion_input=emo_in,
                num_rec=condition.recommendation_count,
                sampling_size=div_sample_size,
                item_pool_size=DIVERSE_N_TUNING_PARAMS['diversity_sample_size'],
                scale_vector=DIVERSE_N_TUNING_PARAMS['scale_vector'],
                lowval=DIVERSE_N_TUNING_PARAMS['low_val'],
                highval=DIVERSE_N_TUNING_PARAMS['high_val'],
                ranking_strategy=DIVERSE_N_TUNING_PARAMS['ranking_strategy'],
                div_crit=DIVERSE_N_TUNING_PARAMS['diversity_criteria'],
                # dist_method=DIVERSE_N_TUNING_PARAMS['distance_method'],
            )

    elif isinstance(ers_control_input[0], EmotionContinuousInputSchema):
        emo_in = [EmotionContinuousInputSchema.model_validate(emoin) for emoin in ers_control_input]
        if condition in [1, 2, 3, 4]:
            recs = ers_recs_service.predict_continuous_tuned_topN(
                user_id=str(participant.id),
                ratings=ratings_with_movielens_ids,
                emotion_input=emo_in,
                num_rec=condition.recommendation_count,
                item_pool_size=TOP_N_TUNING_PARAMS['item_pool_size'],
                scale_vector=TOP_N_TUNING_PARAMS['scale_vector'],
                algo=TOP_N_TUNING_PARAMS['ranking_strategy'],
                dist_method=TOP_N_TUNING_PARAMS['distance_method'],
            )
    recs = [str(rec) for rec in recs if rec is not None]
    if len(recs) == 0:
        raise HTTPException(status_code=406, detail='User condition not found')

    movies = await movie_service.get_movies_with_emotions_by_movielens_ids(recs)
    print('MOVIE ', movies[0].__dict__)
    return [MovieDetailSchema.model_validate(movie) for movie in movies]
