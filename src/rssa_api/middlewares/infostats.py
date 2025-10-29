import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestHandlingStatsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        content_length = request.headers.get('content-length')
        body_size = int(content_length) if content_length else 0

        try:
            response = await call_next(request)
        finally:
            end_time = time.time()
            elapsed_time = end_time - start_time
            request_stats = {
                'method': request.method,
                'path': request.url.path,
                'client': request.client,
                'body_size': body_size,
                'elapsed': elapsed_time,
            }
            logger.info(f'Request Stats: {request_stats}')
        return response
