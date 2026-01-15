"""Study API application configuration."""

import uuid
from datetime import datetime

from fastapi import FastAPI

from rssa_api.core.config import ROOT_PATH

from .routers.recommendations import router as recommendations_router
from .routers.studies import feedback, movies, pages, participant, steps, studies
from .routers.studies.participant_responses import participant_responses

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
    version='0.12.0',
    state={'CACHE': {}, 'CACHE_LIMIT': 100, 'queue': []},
    security=[{'Study ID': []}],
    json_encoders={
        uuid.UUID: lambda obj: str(obj),
        datetime: lambda dt: dt.isoformat(),
    },
)

print(f'{ROOT_PATH}/study/openapi.json')





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
api.include_router(recommendations_router)
api.include_router(participant_responses.router)
