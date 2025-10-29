import logging
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from rssa_api.apps import admin_api, demo_api, study_api
from rssa_api.config import ROOT_PATH
from rssa_api.core.config import configure_logging
from rssa_api.middlewares.bad_request_logging import BadRequestLoggingMiddleware
from rssa_api.middlewares.infostats import RequestHandlingStatsMiddleware
from rssa_api.middlewares.logging import LoggingMiddleware

configure_logging()
logger = logging.getLogger(__name__)

"""
FastAPI App
"""
app = FastAPI(
    root_path=ROOT_PATH,
    # openapi_tags=tags_metadata,
    title='Recommender Systems for Self Actualization',
    # summary=App_Meta.summary,
    # description=App_Meta.description,
    version='0.2.0',
    terms_of_service='https://rssa.recsys.dev/terms',
    docs_url=None,
    redoc_url=None,
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
origins = [
    'http://localhost:3330',
    'http://localhost:3330/*',
    'http://localhost:3339',
    'http://localhost:3339/*',
    'http://localhost:3331',
    'http://localhost:3340',
    'http://localhost:3350',
    'http://localhost:3000',
    'http://localhost:3370',
]

app.mount('/study', study_api)
app.mount('/admin', admin_api, 'RSSA Admin API')
app.mount('/demo', demo_api)

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
# app.add_middleware(RequestHandlingStatsMiddleware)
# app.add_middleware(BadRequestLoggingMiddleware)
# app.add_middleware(LoggingMiddleware)


@app.get('/')
async def root():
    """
    Hello World!
    """
    return {'message': 'Hello World! Welcome to RSSA APIs!'}
