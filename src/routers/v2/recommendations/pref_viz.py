import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from compute.rspv import PreferenceVisualization
from compute.utils import (
	get_pref_viz_data,
	get_pref_viz_model_path,
)
from data.schemas.movie_schemas import MovieSchema
from data.schemas.preferences_schemas import (
	PreferenceRequestSchema,
	PrefVizDemoRequestSchema,
	PrefVizDemoResponseSchema,
	PrefVizItem,
	PrefVizMetadata,
)
from data.schemas.study_schemas import StudySchema
from data.services import MovieService, StudyConditionService
from data.services.content_dependencies import get_movie_service
from data.services.rssa_dependencies import get_study_condition_service as study_condition_service
from docs.metadata import RSTagsEnum as Tags
from routers.v2.resources.study import get_current_registered_study

router = APIRouter(
	prefix='/v2',
	tags=[Tags.rssa],
)


class PrefVizMovieItemSchema(MovieSchema, PrefVizItem):
	pass


CACHE_LIMIT = 100
queue = []
CACHE = {}


@router.post('/demo/prefviz/recommendation/', response_model=PrefVizDemoResponseSchema)
async def create_recommendations(request_model: PrefVizDemoRequestSchema):
	if request_model in CACHE:
		print('Found request in cache. Returning cached response.')
		return CACHE[request_model]

	item_pop, avg_score = get_pref_viz_data()
	model_path = get_pref_viz_model_path()
	pref_viz = PreferenceVisualization(model_path, item_pop, avg_score)
	# def predict_diverse_items(self, ratings: List[RatedItemSchema],\
	# num_rec: int, user_id:int, algo:str='fishnet', randomize:bool=False,\
	# init_sample_size:int=500, min_rating_count:int=50) \
	# -> List[PreferenceItem]:
	recs = pref_viz.predict_diverse_items(
		request_model.ratings,
		request_model.num_rec,
		str(request_model.user_id),
		request_model.algo,
		request_model.randomize,
		request_model.init_sample_size,
		request_model.min_rating_count,
	)
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail='User condition not found')

	res = PrefVizDemoResponseSchema(
		metadata=PrefVizMetadata(
			algo=request_model.algo,
			randomize=request_model.randomize,
			init_sample_size=request_model.init_sample_size,
			min_rating_count=request_model.min_rating_count,
			num_rec=request_model.num_rec,
		),
		recommendations=recs,
	)

	print('Updating cache')
	if len(queue) >= CACHE_LIMIT:
		del CACHE[queue.pop(0)]
	CACHE[request_model] = res
	queue.append(request_model)

	return res


@router.post('/recommendation/prefviz/', response_model=List[PrefVizMovieItemSchema])
async def recommend_for_study_condition(
	request_model: PreferenceRequestSchema,
	study: Annotated[StudySchema, Depends(get_current_registered_study)],
	movie_service: Annotated[MovieService, Depends(get_movie_service)],
	condition_service: Annotated[StudyConditionService, Depends(study_condition_service)],
):
	rateditms = request_model.ratings
	sorted_ratings = sorted(rateditms, key=lambda x: x.item_id)
	cache_key = (
		request_model.user_id,
		tuple(sorted_ratings),
		request_model.user_condition,
		request_model.rec_type,
		study.id,
	)
	if cache_key in CACHE:
		print('Found request in cache. Returning cached response.')
		return CACHE[cache_key]

	item_pop, avg_score = get_pref_viz_data()
	model_path = get_pref_viz_model_path()
	pref_viz = PreferenceVisualization(model_path, item_pop, avg_score)

	# study_condition_service = StudyConditionService(rssadb)
	study_condition = await condition_service.get_study_condition(request_model.user_condition)

	if not study_condition or study_condition.study_id != study.id:
		raise HTTPException(status_code=404, detail='Study condition not found')

	algo = 'fishnet + single_linkage'
	randomize = False
	init_sample_size = 500
	min_rating_count = 50
	recs = []
	if request_model.rec_type == 'baseline':
		recs = pref_viz.get_baseline_prediction(
			request_model.ratings,
			str(request_model.user_id),
			study_condition.recommendation_count,  # type: ignore
		)
	elif request_model.rec_type == 'diverse':
		# FIXME: These values are hardcoded for now but should be fetched from the
		# study condition or a study manifest

		recs = pref_viz.predict_diverse_items(
			request_model.ratings,
			study_condition.recommendation_count,  # type: ignore
			str(request_model.user_id),
			algo,
			randomize,
			init_sample_size,
			min_rating_count,
		)
	elif request_model.rec_type == 'reference':
		recs = pref_viz.predict_reference_items(
			request_model.ratings,
			study_condition.recommendation_count,
			str(request_model.user_id),
			init_sample_size,
			min_rating_count,
		)

	if len(recs) == 0:
		raise HTTPException(status_code=500, detail='No recommendations were generated.')

	recmap = {r.item_id: r for r in recs}
	movies = await movie_service.get_movies_by_movielens_ids(list(recmap.keys()))

	res = []

	for m in movies:
		movie = MovieSchema.model_validate(m)
		pref_item = PrefVizMovieItemSchema(**movie.model_dump(), **recmap[m.movielens_id].model_dump())  # type: ignore
		res.append(pref_item)

	if len(queue) >= CACHE_LIMIT:
		old_key = queue.pop(0)
		del CACHE[old_key]
	CACHE[cache_key] = res
	queue.append(cache_key)

	return res
