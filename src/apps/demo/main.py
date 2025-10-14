# import logging
import uuid
from datetime import datetime

from fastapi import FastAPI

from .routers import movies, recommendations

# from core.config import configure_logging

# configure_logging()
# logger = logging.getLogger(__name__)

"""
RSSA public API endpoints
"""
api = FastAPI(
    title='RSSA API',
    summary='API for all the RSSA projects, that are mainly used by the study clients.',
    description="""
		The API is used to manage the study, the participants, the movie metadata, and
		the specific recommendations for each of the studies.
		""",
    # openapi_tags=tags_metadata,
    version='2.0.0',
    state={'CACHE': {}, 'CACHE_LIMIT': 100, 'queue': []},
    security=[{'Study ID': []}],
    json_encoders={
        uuid.UUID: lambda obj: str(obj),
        datetime: lambda dt: dt.isoformat(),
    },
)

api.include_router(movies.router)
api.include_router(recommendations.router)
