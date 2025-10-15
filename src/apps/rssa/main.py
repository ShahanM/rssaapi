import logging
import uuid
from datetime import datetime

from fastapi import FastAPI

from logging_config import configure_logging

from .routers.recommendations import alt_algo, iers, pref_comm, pref_viz
from .routers.studies import feedback, movies, pages, participant, steps, studies
from .routers.studies.participant_responses import participant_responses

configure_logging()
logger = logging.getLogger(__name__)

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

"""
Resources API Routers
"""
api.include_router(studies.router)
api.include_router(steps.router)
api.include_router(movies.router)
api.include_router(participant.router)
api.include_router(feedback.router)
api.include_router(pages.router)

"""
Recommender API Routers
"""
api.include_router(alt_algo.router)
api.include_router(pref_viz.router)
api.include_router(iers.router)
api.include_router(pref_comm.router)
api.include_router(participant_responses.router)
