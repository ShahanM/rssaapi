"""Admin API entry point."""

import uuid
from datetime import datetime

from fastapi import FastAPI
from starlette.types import ASGIApp

from .docs import admin_tags_metadata
from .routers import movies as movie_admin
from .routers import users as admin_users
from .routers.study_components import authorizations as auth_admin
from .routers.study_components import studies as study_admin
from .routers.study_components import study_conditions as condition_admin
from .routers.study_components import study_step_page_contents as survey_admin
from .routers.study_components import study_step_pages as page_admin
from .routers.study_components import study_steps as step_admin
from .routers.survey_constructs import (
    survey_constructs_router,
    survey_items_router,
    survey_scale_levels_router,
    survey_scales_router,
)

"""
Admin routes
"""
api: ASGIApp = FastAPI(
    title='RSSA - Admin API',
    summary='Protected endpoints for the RSSA Dashboard, Study Control Panel, and the Survey Construct database.',
    description="""
	All endpoints in this API require authentication, and specific permissions granted to the user.
	""",
    openapi_tags=admin_tags_metadata,
    version='0.9.0',
    state={'CACHE': {}, 'CACHE_LIMIT': 100, 'queue': []},
    json_encoders={
        uuid.UUID: lambda obj: str(obj),
        datetime: lambda dt: dt.isoformat(),
    },
)


"""
Admin routers
"""
api.include_router(study_admin.router)
api.include_router(step_admin.router)
api.include_router(page_admin.router)
api.include_router(condition_admin.router)
api.include_router(condition_admin.router)
api.include_router(survey_admin.router)
api.include_router(auth_admin.router)
api.include_router(admin_users.router)
api.include_router(movie_admin.router)

# Survey construct routers
api.include_router(survey_constructs_router)
api.include_router(survey_items_router)
api.include_router(survey_scales_router)
api.include_router(survey_scale_levels_router)
