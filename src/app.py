import logging
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

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
from routers.v2.admin import auth0
from routers.v2.admin import construct_items as items_admin
from routers.v2.admin import construct_scales as scales_admin
from routers.v2.admin import scale_levels as level_admin
from routers.v2.admin import step_pages as page_admin
from routers.v2.admin import studies as study_admin
from routers.v2.admin import study_conditions as condition_admin
from routers.v2.admin import study_steps as step_admin
from routers.v2.admin import survey_constructs as construct_admin
from routers.v2.admin import survey_pages as survey_admin
from routers.v2.admin import users as admin_users
from routers.v2.recommendations import alt_algo, iers, pref_comm, pref_viz
from routers.v2.resources import (
	feedback,
	movies,
	participant,
	participant_response,
	steps,
	studies,
)

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
	version='0.2.0',
	terms_of_service='https://rssa.recsys.dev/terms',
	state={'CACHE': {}, 'CACHE_LIMIT': 100, 'queue': []},
	security=[{'Study ID': []}],
	json_encoders={
		uuid.UUID: lambda obj: str(obj),
		datetime: lambda dt: dt.isoformat(),
	},
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
	'http://localhost:3350',
	'http://localhost:3000',
	'http://192.68.0.21:3330',
	'http://192.68.0.21:3330/*',
]


"""
v2 routers # we will remove v1 once we are done migrating the emotions study code
"""
# app.include_router(admin.router)
app.include_router(auth0.router)
app.include_router(study_admin.router)
app.include_router(step_admin.router)
app.include_router(page_admin.router)
app.include_router(condition_admin.router)
app.include_router(items_admin.router)
app.include_router(scales_admin.router)
app.include_router(construct_admin.router)
app.include_router(level_admin.router)
app.include_router(survey_admin.router)
app.include_router(admin_users.router)
"""
Resources API Routers
"""
app.include_router(studies.router)
app.include_router(movies.router)
app.include_router(participant.router)
app.include_router(steps.router)
app.include_router(feedback.router)

"""
Recommender API Routers
"""
app.include_router(alt_algo.router)
app.include_router(pref_viz.router)
app.include_router(iers.router)
app.include_router(pref_comm.router)
app.include_router(participant_response.router)


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
