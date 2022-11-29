from typing import List
from fastapi import FastAPI, Depends, Body, APIRouter
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from data.database import SessionLocal, engine
from data.models.schema import MovieSchema, RatedItemSchema, RatingsSchema
from data.movies import get_movies, get_movie, get_movies_by_ids, get_ers_movies, get_ers_movies_by_ids
from fastapi.middleware.cors import CORSMiddleware
from compute.rssa import RSSACompute
from compute.utils import *
from router import cybered
from router import iers

# app = FastAPI(root_path='/newrs/api/v1')
app = FastAPI()

rssa_itm_pop, rssa_ave_scores = get_rssa_data()
rssa_model_path = get_rssa_model_path()
rssalgs = RSSACompute(rssa_model_path, rssa_itm_pop, rssa_ave_scores)

origins = [
    "https://cybered.recsys.dev",
    "https://cybered.recsys.dev/*",
    "http://localhost:3000",
    "http://localhost:3000/*",
]

app.include_router(cybered.router)
app.include_router(iers.router)

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
    recs = rssalgs.get_condition_prediction(rated_movies.ratings, \
            rated_movies.user_id, rated_movies.rec_type, rated_movies.num_rec)
    movies = get_movies_by_ids(db, recs)
    
    return movies
