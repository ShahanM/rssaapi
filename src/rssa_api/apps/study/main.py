import uuid
from datetime import datetime

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

from rssa_api.config import ROOT_PATH

from .routers.legacy_recommendations import alt_algo, iers, pref_comm, pref_viz
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
    # openapi_tags=tags_metadata,
    version='0.12.0',
    state={'CACHE': {}, 'CACHE_LIMIT': 100, 'queue': []},
    swagger_ui_parameters={
        'swagger_css_url': f'{ROOT_PATH}/static/swagger-ui-custom.css',
        'syntaxHighlight': {'theme': 'obsidian'},
    },
    security=[{'Study ID': []}],
    json_encoders={
        uuid.UUID: lambda obj: str(obj),
        datetime: lambda dt: dt.isoformat(),
    },
)

print(f'{ROOT_PATH}/study/openapi.json')


@api.get('/docs', include_in_schema=False)
async def custom_swagger_ui_html_cdn():
    return get_swagger_ui_html(
        openapi_url=f'{ROOT_PATH}/study/openapi.json',
        title=f'{api.title} - Swagger U',
        # swagger_ui_dark.css CDN link
        swagger_css_url='https://cdn.jsdelivr.net/gh/Itz-fork/Fastapi-Swagger-UI-Dark/assets/swagger_ui_dark.min.css',
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
api.include_router(recommendations_router)
api.include_router(alt_algo.router)
api.include_router(pref_viz.router)
api.include_router(iers.router)
api.include_router(pref_comm.router)
api.include_router(participant_responses.router)
