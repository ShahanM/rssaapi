from typing import List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
# from sqlalchemy.orm import Session

from compute.utils import *
# from data.moviedatabase import SessionLocal # FIXME: Move to own file

# from data.models.schema.movieschema import MovieSchema
# from router.v1 import (
# 	movies as movies_v1,
# 	users as users_v1, 
# 	admin, 
# 	study as study_v1,
# 	iers,
# 	pref_comm
# )
# from router.v1.admin import get_current_active_user, AdminUser

from router.v2 import (
	study as study_v2,
	movies,
	study_meta,
	auth0,
	pref_viz,
	participant,
	alt_algo,
	pref_comm as pref_comm_v2
)


# from data.movies import get_movies, get_movies_by_ids
from middleware.error_handlers import ErrorHanlingMiddleware
from middleware.infostats import RequestHandlingStatsMiddleware
from middleware.access_logger import LoggingMiddleware

from docs.metadata import (
	tags_metadata,
	TagsMetadataEnum as Tags,
	AppMetadata as App_Meta
)


"""
FastAPI App
"""
# TODO: Move string values to a config file
app = FastAPI(
	root_path='/rssa/api',
	root_path_in_servers=False,
	openapi_tags=tags_metadata,
	title=App_Meta.title,
	summary=App_Meta.summary,
	description=App_Meta.description,
	version='0.1.0',
	terms_of_service='https://rssa.recsys.dev/terms'
)


"""
CORS Origins
"""
# TODO: Move to a config file
origins = [
    'https://cybered.recsys.dev',
    'https://cybered.recsys.dev/*',
    'http://localhost:3330',
	'http://localhost:3330/*',
	'http://localhost:3339',
    'http://localhost:3339/*',
	'http://localhost:3331',
	'http://localhost:3340',
	'http://localhost:3000'
]


"""
v1 routers
"""
# app.include_router(study_v1.router)
# app.include_router(users_v1.router)
# app.include_router(movies_v1.router)
# app.include_router(iers.router)
# app.include_router(pref_comm.router) # FIXME: move to v1 module
# app.include_router(admin.router)


"""
v2 routers
"""
app.include_router(study_v2.router)
app.include_router(alt_algo.router)
app.include_router(pref_viz.router)
app.include_router(study_meta.router)
app.include_router(participant.router)
app.include_router(movies.router)
app.include_router(auth0.router)
app.include_router(pref_comm_v2.router)


"""
Middlewares
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(ErrorHanlingMiddleware)
app.add_middleware(RequestHandlingStatsMiddleware)
app.add_middleware(LoggingMiddleware)


# Dependency
# def get_db():
# 	db = SessionLocal()
# 	try:
# 		yield db
# 	finally:
# 		db.close()


@app.get('/')
async def root():
	"""
	Hello World!
	"""
	return {'message': 'Hello World'}


# @app.get('/data/all/', include_in_schema=False)
# async def get_data_zip(
# 	current_user: AdminUser = Depends(get_current_active_user)):
# 	"""
# 	Downloads a zip file containing data files and models to bootstrap the
# 	project template for the Advanced Decision Support Systems course taught by
# 	Dr. Bart Knijnenburg during the Fall 2022 semester.
	
# 	Returns a a zip file containing the data files and models.
# 	"""
# 	return FileResponse('datafiles/rssa_all.zip',
# 						media_type='application/octet-stream',
# 						filename='data/rssa_all.zip')


# @app.get(
# 	'/movies/',
# 	response_model=List[MovieSchema],
# 	tags=[Tags.movie])
# async def read_movies(skip: int=0, limit: int=100, db: Session=Depends(get_db)):
# 	movies = get_movies(db, skip=skip, limit=limit) # type: ignore
	
# 	return movies

