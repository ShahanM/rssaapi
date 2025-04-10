from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from compute.utils import *
from docs.metadata import AppMetadata as App_Meta
from docs.metadata import tags_metadata
from middleware.access_logger import LoggingMiddleware
from middleware.error_handlers import ErrorHanlingMiddleware
from middleware.infostats import RequestHandlingStatsMiddleware
from router.v2 import (
	alt_algo,
	auth0,
	movies,
	participant,
	pref_viz,
	study_meta,
	iers,
	pref_comm as pref_comm_v2,
	study as study_v2,
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
	terms_of_service='https://rssa.recsys.dev/terms',
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
	'http://localhost:3000',
]


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
app.include_router(iers.router)


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
