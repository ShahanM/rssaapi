import uuid
from datetime import datetime

from fastapi import FastAPI
from starlette.types import ASGIApp

from rssa_api.middlewares.access_logger import DashboardAccessLogMiddleware

from .docs import admin_tags_metadata
from .routers import construct_items as items_admin
from .routers import construct_scales as scales_admin
from .routers import movies as movie_admin
from .routers import scale_levels as level_admin
from .routers import step_pages as page_admin
from .routers import studies as study_admin
from .routers import study_conditions as condition_admin
from .routers import study_steps as step_admin
from .routers import survey_constructs as construct_admin
from .routers import survey_pages as survey_admin
from .routers import users as admin_users

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
api.include_router(items_admin.router)
api.include_router(scales_admin.router)
api.include_router(construct_admin.router)
api.include_router(level_admin.router)
api.include_router(survey_admin.router)
api.include_router(admin_users.router)
api.include_router(movie_admin.router)

# api.add_middleware(DashboardAccessLogMiddleware)
