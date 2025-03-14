from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from compute.rspv import PreferenceVisualization, PreferenceItem, RatedItemSchema
from compute.utils import *
from data.moviedb import get_db as movie_db
from data.rssadb import get_db as rssa_db
from data.models.schema.movieschema import BaseModel
# from data.movies import *
from data.studies_v2 import Study
from .study import get_current_registered_study
from data.accessors.studies import get_study_condition
from compute.rssa import AlternateRS
from data.models.schema.movieschema import MovieSchema, RatingSchemaV2, MovieSchemaV2

import uuid


router = APIRouter(prefix='/v2')


@router.post('/recommendation/', response_model=List[MovieSchemaV2])
async def create_recommendations(rated_movies: RatingSchemaV2, db: Session=Depends(movie_db)):
	rssa_itm_pop, rssa_ave_scores = get_rssa_ers_data()
	rssa_model_path = get_rssa_model_path()
	rssalgs = AlternateRS(rssa_model_path, rssa_itm_pop, rssa_ave_scores)
	recs = rssalgs.get_condition_prediction(\
			ratings=rated_movies.ratings, \
			user_id=str(rated_movies.user_id), \
			condition=rated_movies.rec_type, \
			num_rec=rated_movies.num_rec)
	
	movies = get_ers_movies_by_movielens_ids(db, recs)

	return movies