"""Main entrypoint for the RSSA API."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from rssa_api.apps import admin_api, demo_api, study_api
from rssa_api.core.config import CORS_ORIGINS, PROJECT_ROOT, ROOT_PATH
from rssa_api.core.logging import configure_structlog
from rssa_api.core.middleware import StructlogAccessMiddleware
from rssa_api.data.workers import db_writer_worker

logger = structlog.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    configure_structlog()
    logger.info('Starting up RSSA API...')
    worker_task = asyncio.create_task(db_writer_worker())
    yield

    logger.info('Shutting down RSSA API...')
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logger.error('Could not cancel db session worker.')


app = FastAPI(
    title='Recommender Systems for Self Actualization',
    version='0.2.0',
    terms_of_service='https://rssa.recsys.dev/terms',
    root_path=ROOT_PATH,
    lifespan=lifespan,
    state={'CACHE': {}, 'CACHE_LIMIT': 100, 'queue': []},
    security=[{'Study ID': []}],
    json_encoders={
        uuid.UUID: lambda obj: str(obj),
        datetime: lambda dt: dt.isoformat(),
    },
)

static_dir = PROJECT_ROOT / 'src' / 'rssa_api' / 'static'
if static_dir.exists():
    app.mount('/static', StaticFiles(directory=static_dir), name='static')
else:
    logger.warning(f'Static directory not found at {static_dir}')


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
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


app.mount('/study', study_api)
app.mount('/admin', admin_api, 'RSSA Admin API')
app.mount('/demo', demo_api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r'^https://rssa-.*(\.recsys\.dev|-recsys-dev\.pages\.dev)$',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(StructlogAccessMiddleware)


@app.get('/')
async def root():
    """Root endpoint."""
    return {'message': 'Hello World! Welcome to RSSA APIs!'}
