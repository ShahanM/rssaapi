from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from compute.rssa import AlternateRS
from compute.utils import get_rssa_ers_data, get_rssa_model_path
from data.moviedb import get_db as movie_db
from data.schemas.movie_schemas import MovieSchema
from data.schemas.preferences_schemas import PreferenceRequestSchema
from data.services.movie_service import MovieService
from docs.metadata import RSTagsEnum as Tags

router = APIRouter(
    prefix='/v2',
    tags=[Tags.rssa],
)


@router.post('/recommendation/', response_model=List[MovieSchema])
async def generate_alt_recommendations(user_ratings: PreferenceRequestSchema, db: Session = Depends(movie_db)):
    """_summary_

    Args:
            rated_movies (RatingSchemaV2): _description_
            db (Session, optional): _description_. Defaults to Depends(movie_db).

    Returns:
            _type_: _description_
    """
    rssa_itm_pop, rssa_ave_scores = get_rssa_ers_data()
    rssa_model_path = get_rssa_model_path()
    rssalgs = AlternateRS(rssa_model_path, rssa_itm_pop, rssa_ave_scores)
    recs = rssalgs.get_condition_prediction(
        ratings=user_ratings.ratings,
        user_id=str(user_ratings.user_id),
        condition=user_ratings.user_condition,
        num_rec=user_ratings.num_rec,
    )

    movies = get_ers_movies_by_movielens_ids(db, recs)

    return movies
