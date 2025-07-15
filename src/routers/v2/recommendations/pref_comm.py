from typing import Annotated, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from compute.rspc import PreferenceCommunity
from compute.utils import get_rating_data_path, get_rssa_ers_data, get_rssa_model_path
from data.schemas.movie_schemas import MovieSchema
from data.schemas.preferences_schemas import PrefCommRatingSchema
from data.services import MovieService
from data.services.content_dependencies import get_movie_service
from docs.metadata import RSTagsEnum as Tags

router = APIRouter(
	prefix='/v2',
	tags=[Tags.rssa],
)


class AdvisorIDSchema(BaseModel):
	advisor_id: int


# class MovieRecommedantion(MovieSchema, MovieRecommendationSchema):
# pass


class AdvisorProfileSchema(BaseModel):
	id: str
	movies: List[MovieSchema]
	recommendation: MovieSchema


@router.post('/recommendations/advisors/', response_model=List[AdvisorProfileSchema])
async def get_advisor(
	rated_movies: PrefCommRatingSchema,
	movie_service: Annotated[MovieService, Depends(get_movie_service)],
):
	rssa_itm_pop, rssa_ave_scores = get_rssa_ers_data()
	rssa_model_path = get_rssa_model_path()
	rssa_pref_comm = PreferenceCommunity(rssa_model_path, rssa_itm_pop, rssa_ave_scores, get_rating_data_path())

	advisors = []

	recs = rssa_pref_comm.get_advisors_with_profile(rated_movies.ratings, rated_movies.user_id, num_rec=7)

	for adv, value in recs.items():
		profile_movies = await movie_service.get_movies_by_movielens_ids([str(val) for val in value['profile_top']])
		recommendation = await movie_service.get_movie_by_movielens_id(str(value['recommendation']))
		# recommendation = recommendation[0]

		# rec_details = await get_movie_recommendation_text(db, recommendation.id)

		# if rec_details is not None:
		# 	movie_rec_dict = recommendation.model_dump()
		# 	movie_rec_dict.update(rec_details.model_dump())
		# 	movie_rec = MovieRecommedantion(**movie_rec_dict)

		# advprofile = AdvisorProfileSchema(id=str(adv), movies=profile_movies, recommendation=movie_rec)
		validated_movies = [MovieSchema.model_validate(m) for m in profile_movies]
		validated_rec = MovieSchema.model_validate(recommendation)
		advprofile = AdvisorProfileSchema(id=str(adv), movies=validated_movies, recommendation=validated_rec)
		advisors.append(advprofile)

	return advisors
