import logging
import time
from typing import Union

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from data.logger import log_access

# from data.rssadb import get_db as rssadb
from data.rssadb import RSSADatabase

access_logger = logging.getLogger('dashboard_access')


class DashboardAccessLogMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: Request, call_next):
		start_time = time.time()
		response = await call_next(request)
		process_time = time.time() - start_time

		if request.url.path.startswith('/meta/'):
			auth0_user_obj = getattr(request.state, 'auth0_user', None)
			if auth0_user_obj:
				auth0_user_id = auth0_user_obj.sub
				action = request.method.lower()
				resource = request.url.path.split('/')[2]
				resource_id = None
				if len(request.url.path.split('/')) > 3:
					resource_id = request.url.path.split('/')[3]

				# async with rssadb() as db:
				async with RSSADatabase() as db:
					await log_access(db, auth0_user_id, action, resource, resource_id)
			else:
				access_logger.warning(f'No auth0_user found in request.state for path: {request.url.path}')

		return response


class APIAccessLogMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: Request, call_next):
		start_time = time.time()
		response = await call_next(request)
		process_time = time.time() - start_time

		# Define which API paths you want to log (e.g., exclude health checks)
		if not request.url.path.startswith('/docs') and not request.url.path.startswith('/openapi.json'):
			user_identifier = 'anonymous'  # Default if no user identified

			# Attempt to extract user information based on your authentication mechanism
			# Example: Extracting from a token header
			# token = request.headers.get("Authorization")
			# if token and token.startswith("Bearer "):
			#     try:
			#         payload = decode_token(token.split(" ")[1])
			#         user_identifier = payload.get("sub", "unknown_user")
			#     except Exception:
			#         access_logger.warning(f"Error decoding token for path: {request.url.path}")

			# Or, if you have study context available in request.state:
			study = getattr(request.state, 'current_study', None)
			if study:
				user_identifier = f'study: {study.name} ({study.id})'

			action = request.method.lower()
			resource = request.url.path.split('?')[0]  # Remove query parameters
			resource_id = None
			path_segments = request.url.path.split('/')
			if len(path_segments) > 2:
				resource_id = path_segments[2]  # Adjust based on your API structure

			async with RSSADatabase() as db:
				await log_access(db, user_identifier, action, resource, resource_id)

			access_logger.info(
				f'API Access: {request.method} {request.url.path} - {response.status_code} ({process_time:.4f}s) - User: {user_identifier}'
			)

		return response
