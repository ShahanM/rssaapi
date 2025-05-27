import logging

from fastapi import HTTPException
from fastapi import Request as FastAPIRequest
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class BadRequestLoggingMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: FastAPIRequest, call_next):
		response = None
		try:
			response = await call_next(request)
			return response
		except ValidationError as e:
			logger.error(f'BadRequestLoggingMiddleware - Validation Error for URL: {request.url}')
			try:
				body = await request.json()
				logger.error(f'BadRequestLoggingMiddleware - Request Body: {body}')
			except Exception:
				logger.error('BadRequestLoggingMiddleware - Could not parse request body as JSON.')
			logger.error(f'BadRequestLoggingMiddleware - Validation Errors: {e.errors()}')
			return JSONResponse(
				status_code=400,
				content={'detail': e.errors()},
			)
		except HTTPException as e:
			if e.status_code == 400:
				logger.error(f'BadRequestLoggingMiddleware - HTTP 400 Bad Request for URL: {request.url}')
				try:
					body = await request.json()
					logger.error(f'BadRequestLoggingMiddleware - Request Body: {body}')
				except Exception:
					logger.error('BadRequestLoggingMiddleware - Could not parse request body as JSON.')
				logger.error(f'BadRequestLoggingMiddleware - Error Detail: {e.detail}')
			raise  # Re-raise
		except Exception as e:
			logger.error(f'BadRequestLoggingMiddleware - Unexpected error for URL: {request.url}', exc_info=True)
			return JSONResponse(
				status_code=500,
				content={'detail': 'Internal Server Error'},
			)
		finally:
			if response is not None and response.status_code == 400:
				logger.warning(f'BadRequestLoggingMiddleware - Saw a 400 response for URL: {request.url}')
