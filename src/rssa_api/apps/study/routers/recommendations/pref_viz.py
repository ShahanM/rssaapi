import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import get_current_participant, validate_api_key
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.schemas.movie_schemas import MovieSchema
from rssa_api.data.schemas.participant_response_schemas import (
    MovieLensRatingSchema,
)
from rssa_api.data.schemas.preferences_schemas import (
    PreferenceVizRecommendedItemSchema,
    PrefVizDemoRequestSchema,
    PrefVizDemoResponseSchema,
    PrefVizMetadata,
    RecommendationContextBaseSchema,
    RecommendationJsonPrefVizSchema,
    RecommendationRequestPayload,
)
from rssa_api.data.services import MovieService, StudyConditionService
from rssa_api.data.services.content_dependencies import get_movie_service as movie_service
from rssa_api.data.services.participant_service import ParticipantService
from rssa_api.data.services.rssa_dependencies import (
    get_participant_service as participant_service,
)
from rssa_api.data.services.rssa_dependencies import get_study_condition_service as study_condition_service
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.services.recommenders.prev_viz_service import PreferenceVisualization

BIASED_MODEL_PATH = 'biased_als_ml32m'
router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)


@router.post('/prefviz', response_model=dict[str, PreferenceVizRecommendedItemSchema])
async def recommend_for_study_condition(
    payload: RecommendationRequestPayload,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
    movie_service: Annotated[MovieService, Depends(movie_service)],
    condition_service: Annotated[StudyConditionService, Depends(study_condition_service)],
    participant_service: Annotated[ParticipantService, Depends(participant_service)],
):
    rec_ctx = await participant_service.get_recommndation_context_by_participant_context(
        study_id, participant.id, payload.context_tag
    )

    if rec_ctx:
        rec_json = rec_ctx.recommendations_json['prefviz_map']
        return rec_json

    condition = await condition_service.get_study_condition(participant.condition_id)
    pref_viz = PreferenceVisualization(BIASED_MODEL_PATH)

    rated_item_dict = {item.item_id: item.rating for item in payload.ratings}
    rated_movies = await movie_service.get_movies_from_ids(list(rated_item_dict.keys()))
    ratings_with_movielens_ids = [
        MovieLensRatingSchema.model_validate({'item_id': item.movielens_id, 'rating': rated_item_dict[item.id]})
        for item in rated_movies
    ]

    algo = 'fishnet + single_linkage'
    init_sample_size = 500
    min_rating_count = 50
    recs = []
    if condition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Participant not assigned a condition')

    if payload.rec_type == 'baseline':
        recs = pref_viz.get_baseline_prediction(
            ratings_with_movielens_ids,
            str(participant.id),
            condition.recommendation_count,
        )
    elif payload.rec_type == 'diverse':
        # FIXME: These values are hardcoded for now but should be fetched from the
        # study condition or a study manifest

        recs = pref_viz.predict_diverse_items(
            ratings_with_movielens_ids,
            condition.recommendation_count,
            str(participant.id),
            algo,
            init_sample_size,
            min_rating_count,
        )
    elif payload.rec_type == 'reference':
        recs = pref_viz.predict_reference_items(
            ratings_with_movielens_ids,
            condition.recommendation_count,
            str(participant.id),
            init_sample_size,
            min_rating_count,
        )

    if len(recs) == 0:
        raise HTTPException(status_code=500, detail='No recommendations were generated.')

    recmap = {r.item_id: r for r in recs}
    movies = await movie_service.get_movies_by_movielens_ids(list(recmap.keys()))

    res = {}

    for m in movies:
        movie = MovieSchema.model_validate(m)
        pref_item = PreferenceVizRecommendedItemSchema(**movie.model_dump(), **recmap[m.movielens_id].model_dump())
        res[str(pref_item.id)] = pref_item

    rec_ctx_create_req = RecommendationContextBaseSchema(
        step_id=payload.step_id,
        step_page_id=payload.step_page_id,
        context_tag=payload.context_tag,
        recommendations_json=RecommendationJsonPrefVizSchema(condition=condition, prefviz_map=res),
    )
    recommendation_context = await participant_service.create_recommendation_context(
        study_id, participant.id, rec_ctx_create_req
    )

    return res
