import logging

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from data.moviedb import movie_db
from docs.metadata import AppMetadata as App_Meta
from docs.metadata import tags_metadata
from logging_config import configure_logging
from middlewares.access_logger import (
	APIAccessLogMiddleware,
	DashboardAccessLogMiddleware,
)
from middlewares.bad_request_logging import BadRequestLoggingMiddleware
from middlewares.infostats import RequestHandlingStatsMiddleware
from middlewares.logging import LoggingMiddleware
from routers.v2.recommendations import alt_algo, iers, pref_comm, pref_viz
from routers.v2.resources import auth0, movies, participant, study, study_meta

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

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
	state={'CACHE': {}, 'CACHE_LIMIT': 100, 'queue': []},
	dependencies=[Depends(movie_db.get_db)],
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
	logger.error(f'Validation Error for URL: {request.url}')
	try:
		body = await request.body()
		logger.error(f'Request Body: {body.decode()}')
	except Exception:
		logger.error('Could not parse request body.')
	logger.error(f'Validation Errors: {exc.errors()}')
	return JSONResponse(
		status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
		content={'detail': exc.errors()},
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
	'https://localhost:3350',
	'http://localhost:3000',
]


"""
v2 routers # we will remove v1 once we are done migrating the emotions study code
"""

"""
Resources API Routers
"""
app.include_router(study.router)
app.include_router(movies.router)
app.include_router(participant.router)
app.include_router(study_meta.router)


"""
Recommender API Routers
"""
app.include_router(alt_algo.router)
app.include_router(pref_viz.router)
app.include_router(iers.router)
app.include_router(auth0.router)
app.include_router(pref_comm.router)


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
app.add_middleware(RequestHandlingStatsMiddleware)
app.add_middleware(BadRequestLoggingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(APIAccessLogMiddleware)
app.add_middleware(DashboardAccessLogMiddleware)


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
