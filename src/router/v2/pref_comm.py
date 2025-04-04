from fastapi import APIRouter, Depends
from docs.metadata import TagsMetadataEnum as Tags
from typing import List
from data.models.schemas.advisorschema import PrefCommRatingSchema
from compute.utils import (
	get_rating_data_path,
	get_rssa_ers_data, get_rssa_model_path
)
from compute.rspc import PreferenceCommunity
from sqlalchemy.orm import Session
from data.models.schemas.movieschema import *
from data.moviedb import get_db as movie_db
from data.accessors.movies import (
	get_ers_movies_by_movielens_ids,
	get_movie_recommendation_text,
	MovieRecommendationSchema
)

router = APIRouter(prefix='/v2', deprecated=True)


class AdvisorIDSchema (BaseModel):
	advisor_id: int


class MovieRecommedantion(MovieSchemaV2, MovieRecommendationSchema):
	pass


class AdvisorProfileSchema (BaseModel):
	id: str
	movies: List[MovieSchemaV2]
	recommendation: MovieRecommedantion


@router.post("/prefComm/advisors/", response_model=List[AdvisorProfileSchema], tags=[Tags.pref_comm])
async def get_advisor(rated_movies: PrefCommRatingSchema, \
	db: Session = Depends(movie_db)):

	rssa_itm_pop, rssa_ave_scores = get_rssa_ers_data()
	rssa_model_path = get_rssa_model_path()
	rssa_pref_comm = PreferenceCommunity(rssa_model_path, rssa_itm_pop, rssa_ave_scores, get_rating_data_path())

	advisors = []
	
	recs = rssa_pref_comm.get_advisors_with_profile(rated_movies.ratings, \
			rated_movies.user_id, num_rec=7)

	for adv, value in recs.items():
		profile_movies = get_ers_movies_by_movielens_ids(db, [str(val) for val in value['profile_top']])
		recommendation = get_ers_movies_by_movielens_ids(db, [str(value['recommendation'])])[0]

		rec_details = get_movie_recommendation_text(db, recommendation.id)
		
		if rec_details is not None:
			movie_rec_dict = recommendation.model_dump()
			movie_rec_dict.update(rec_details.model_dump())
			movie_rec = MovieRecommedantion(**movie_rec_dict)

		advprofile = AdvisorProfileSchema(id=str(adv), movies=profile_movies, recommendation=movie_rec)
		advisors.append(advprofile)

	return advisors
