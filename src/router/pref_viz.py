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

@router.post('/prefviz/recommendation/', response_model=List[PreferenceItem])
async def create_recommendations(rated_movies: RatingsSchema, \
	db: Session = Depends(get_db)):
	item_pop, avg_score = get_pref_viz_data()
	model_path = get_pref_viz_model_path()
	pref_viz = PreferenceVisualization(model_path, item_pop, avg_score)
	print(f'/prefviz/recommendation/: {rated_movies}')
	recs = pref_viz.predict_diverse_items(rated_movies.ratings,\
				rated_movies.num_rec, rated_movies.user_id)
	
	print(len(recs))
	
	if len(recs) == 0:
		raise HTTPException(status_code=406, detail="User condition not found")
	
	return recs