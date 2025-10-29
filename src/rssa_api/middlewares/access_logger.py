import logging
import time

from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware

from rssa_api.auth.security import validate_auth0_token
from rssa_api.config import ROOT_PATH
from rssa_api.data.logger import log_access
from rssa_api.data.rssadb import RSSADatabase

access_logger = logging.getLogger('dashboard_access')


class DashboardAccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get('Authorization')
        scheme, token = get_authorization_scheme_param(auth_header)

        auth0_user = None
        if scheme.lower() == 'bearer' and token:
            try:
                auth0_user = await validate_auth0_token(token)
                request.state.user = auth0_user
            except Exception:
                request.state.user = None
        else:
            request.state.user = None

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        current_user = getattr(request.state, 'user', None)

        if request.url.path.startswith(f'{ROOT_PATH}/admin/') and current_user:
            action = request.method.lower()
            resource = request.url.path.split('?')[0]
            resource_id = None
            path_segments = request.url.path.split('/')
            if len(path_segments) > 2:
                resource_id = path_segments[2]
            async with RSSADatabase() as db:
                await log_access(db, current_user.sub, action, resource, resource_id)

            access_logger.info(
                f'API Access: {request.method} {request.url.path} - {response.status_code}'
                + f'({process_time:.4f}s) - User: {current_user.sub}'
            )

        return response


class APIAccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        if (
            not request.url.path.startswith('/docs')
            and not request.url.path.startswith('/openapi.json')
            and not request.url.path.startswith(f'{ROOT_PATH}/admin')
        ):
            user_identifier = 'anonymous'

            study = getattr(request.state, 'current_study', None)
            if study:
                user_identifier = f'study: {study.name} ({study.id})'

            # action = request.method.lower()
            # resource = request.url.path.split('?')[0]
            # resource_id = None
            # path_segments = request.url.path.split('/')
            # if len(path_segments) > 2:
            # resource_id = path_segments[2]

            # async with RSSADatabase() as db:
            # await log_access(db, user_identifier, action, resource, resource_id)

            access_logger.info(
                f'API Access: {request.method} {request.url.path} - {response.status_code}'
                + f'({process_time:.4f}s) - User: {user_identifier}'
            )

        return response
