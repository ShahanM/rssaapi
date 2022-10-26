from typing import List
from fastapi import FastAPI, Depends, Body, APIRouter
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from data.database import SessionLocal, engine
from data.cybereddatabase import SessionLocal as CyberedSessionLocal, engine as cybered_engine
from data.models.schema import MovieSchema, RatedItemSchema, RatingsSchema
from data.movies import get_movies, get_movie, get_movies_by_ids
from fastapi.middleware.cors import CORSMiddleware
from compute.rssa import RSSACompute
from compute.utils import *

app = FastAPI(root_path='/newrs/api/v1')
rssa = RSSACompute()
# app = FastAPI(root_path='/newrs/api/v1')
app = FastAPI()

rssa_itm_pop, rssa_ave_scores = get_rssa_data()
rssa_model = get_rssa_model()
rssa = RSSACompute(rssa_itm_pop, rssa_ave_scores, rssa_model)

cybered_itm_pop, cybered_ave_scores = get_cybered_data()
cybered_model = get_cybered_model()
cybered = RSSACompute(cybered_itm_pop, cybered_ave_scores, cybered_model) 

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cybered_db():
    db = CyberedSessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/data/all/")
async def get_data_zip():
    return FileResponse('datafiles/rssa_all.zip', \
            media_type='application/octet-stream',\
            filename='data/rssa_all.zip')

@app.get("/movies/", response_model=List[MovieSchema])
async def read_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    movies = get_movies(db, skip=skip, limit=limit)
    return movies

@app.post("/recommendation/", response_model=List[MovieSchema])
async def create_recommendations(rated_movies: RatingsSchema, db: Session = Depends(get_db)):
    recs = rssa.get_condition_prediction(rated_movies.ratings, \
            rated_movies.user_id, rated_movies.rec_type, rated_movies.numRec)
    # recs = rssa.predict_user_topN(rated_movies.ratings, rated_movies.user_id, 10)
    movies = get_movies_by_ids(db, recs)
    
    return movies

@app.get("/cybered/movies/", response_model=List[MovieSchema])
async def read_cybered_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_cybered_db)):
    movies = get_movies(db, skip=skip, limit=limit)
    return movies

@app.post("/cybered/recommendation/", response_model=List[MovieSchema])
async def create_cybered_recommendations(rated_movies: RatingsSchema, db: Session = Depends(get_cybered_db)):
    recs = cybered.get_condition_prediction(rated_movies.ratings, \
            rated_movies.user_id, rated_movies.rec_type, rated_movies.numRec)
    # recs = rssa.predict_user_topN(rated_movies.ratings, rated_movies.user_id, 10)
    movies = get_movies_by_ids(db, recs)
    
    return movies
