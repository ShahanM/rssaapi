import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from compute.rspv import PreferenceItem, PreferenceVisualization, RatedItemSchema
from compute.utils import *

# from data.movies import *
from data.accessors.movies import get_ers_movies_by_movielens_ids
from data.accessors.studies import get_study_condition
from data.logger import Study
from data.models.schemas.movieschema import BaseModel, MovieSchemaV2
from data.moviedb import get_db as movie_db
from data.rssadb import get_db as rssa_db

from .study import get_current_registered_study

router = APIRouter(prefix='/v2')


class PrefVizRequestSchema(BaseModel):
	user_id: int
	user_condition: int
	ratings: List[RatedItemSchema]
	num_rec: int = 10
	algo: str
	randomize: bool
	init_sample_size: int
	min_rating_count: int

	class Config:
		from_attributes = True

	def __hash__(self):
		return self.model_dump_json().__hash__()


class PrefVizRequestSchemaV2(BaseModel):
	user_id: uuid.UUID
	user_condition: uuid.UUID
	ratings: List[RatedItemSchema]

	def __hash__(self):
		return self.model_dump_json().__hash__()


class PrefVizMetadata(BaseModel, frozen=True):
	algo: str
	randomize: bool
	init_sample_size: int
	min_rating_count: int
	num_rec: int


class PrefVizResponseSchema(BaseModel):
	metadata: PrefVizMetadata
	recommendations: List[PreferenceItem]

	class Config:
		from_attributes = True

	def __hash__(self):
		return self.model_dump_json().__hash__()


class PreferenceItemV2(MovieSchemaV2, PreferenceItem):
	pass


class PrefVizResponseSchemaV2(BaseModel):
	metadata: PrefVizMetadata
	recommendations: List[PreferenceItem]

	def __hash__(self):
		return self.model_dump_json().__hash__()


CACHE_LIMIT = 100
queue = []
CACHE = {}


@router.post(
	'/demo/prefviz/recommendation/',
	response_model=PrefVizResponseSchema)
async def create_recommendations(request_model: PrefVizRequestSchema):

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
	recs = pref_viz.predict_diverse_items(request_model.ratings,\
				request_model.num_rec, str(request_model.user_id),\
				request_model.algo, request_model.randomize,\
				request_model.init_sample_size, request_model.min_rating_count)
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail="User condition not found")

	res = PrefVizResponseSchema(\
		metadata=PrefVizMetadata(algo=request_model.algo,\
		randomize=request_model.randomize,\
		init_sample_size=request_model.init_sample_size,\
		min_rating_count=request_model.min_rating_count,\
		num_rec=request_model.num_rec), recommendations=recs)

	print('Updating cache')
	if len(queue) >= CACHE_LIMIT:
		del CACHE[queue.pop(0)]
	CACHE[request_model] = res
	queue.append(request_model)

	return res


@router.post(
		'/prefviz/recommendation/',
		response_model=List[PreferenceItemV2])
async def recommend_for_study_condition(
	request_model: PrefVizRequestSchemaV2,
	db: Session = Depends(rssa_db),
	study: Study = Depends(get_current_registered_study),
	movie_db: Session = Depends(movie_db)):

	if request_model in CACHE:
		print('Found request in cache. Returning cached response.')
		return CACHE[request_model]

	item_pop, avg_score = get_pref_viz_data()
	model_path = get_pref_viz_model_path()
	pref_viz = PreferenceVisualization(model_path, item_pop, avg_score)

	study_condition = get_study_condition(db, request_model.user_condition)
	if not study_condition or study_condition.study_id != study.id: # type: ignore
		raise HTTPException(status_code=404, detail='Study condition not found')

	# FIXME: These values are hardcoded for now but should be fetched from the
	# study condition or a study manifest
	algo = 'fishnet + single_linkage'
	randomize = False
	init_sample_size = 500
	min_rating_count = 50

	recs = pref_viz.predict_diverse_items(
				request_model.ratings,
				study_condition.recommendation_count, # type: ignore
				str(request_model.user_id),
				algo,
				randomize,
				init_sample_size,
				min_rating_count)

	if len(recs) == 0:
		raise HTTPException(status_code=500, detail='No recommendations were generated.')

	recmap = {r.item_id: r for r in recs}
	movies = get_ers_movies_by_movielens_ids(movie_db, list(recmap.keys()))

	res = []

	for m in movies:
		movie = MovieSchemaV2.model_validate(m)
		pref_item = PreferenceItemV2(**movie.model_dump(), **recmap[m.movielens_id].model_dump()) # type: ignore
		res.append(pref_item)

	if len(queue) >= CACHE_LIMIT:
		del CACHE[queue.pop(0)]
	CACHE[request_model] = res
	queue.append(request_model)

	return res
