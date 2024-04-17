from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from compute.rspv import PreferenceVisualization, PreferenceItem
from compute.utils import *
from data.moviedatabase import SessionLocal
from data.models.schema.movieschema import *
from data.movies import *


router = APIRouter()

# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

class PrefVizRequestSchema(BaseModel):
	ratings: List[RatedItemSchema]
	num_rec: int = 10
	user_id: int
	user_condition: int
	algo: str
	randomize: bool
	init_sample_size: int
	min_rating_count: int

	class Config:
		orm_mode = True

	def __hash__(self):
		return self.json().__hash__()


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
		orm_mode = True

	def __hash__(self):
		return self.json().__hash__()


CACHE_LIMIT = 100
queue = []
CACHE = {}


@router.post('/prefviz/recommendation/', response_model=PrefVizResponseSchema)
async def create_recommendations(request_model: PrefVizRequestSchema, \
	db: Session = Depends(get_db)):

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
				request_model.num_rec, request_model.user_id,\
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
