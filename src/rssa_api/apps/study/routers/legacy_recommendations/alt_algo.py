import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from rssa_api.auth.authorization import get_current_participant, validate_api_key
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.schemas.movie_schemas import MovieSchema
from rssa_api.data.schemas.participant_schemas import StudyParticipantRead
from rssa_api.data.schemas.preferences_schemas import (
    RecommendationRequestPayload,
)
from rssa_api.data.services import MovieServiceDep, StudyConditionServiceDep, StudyParticipantServiceDep
from rssa_api.docs.metadata import RSTagsEnum as Tags
from rssa_api.services.recommendation.alt_rec_service import AlternateRS

IMPLICIT_MODEL_PATH = 'implicit_als_ml32m'
router = APIRouter(
    prefix='/recommendations',
    tags=[Tags.rssa],
)

CONDITIONS_MAP = {'topN': 0, 'controversial': 1, 'hate': 2, 'hip': 3, 'noclue': 4}


@router.post('/recommendation/', response_model=list[MovieSchema])
async def generate_alt_recommendations(
    payload: RecommendationRequestPayload,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
    participant: Annotated[StudyParticipant, Depends(get_current_participant)],
    movie_service: MovieServiceDep,
    condition_service: StudyConditionServiceDep,
    participant_service: StudyParticipantServiceDep,
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
