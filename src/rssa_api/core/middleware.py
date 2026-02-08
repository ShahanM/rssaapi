"""Middleware for the RSSA API."""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class StructlogAccessMiddleware(BaseHTTPMiddleware):
    """Middleware to log access requests using structlog."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and log access details."""
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter_ns()

        try:
            response = await call_next(request)
        except Exception as e:
            # Check for database connection errors
            error_str = str(e)
            if 'connection is closed' in error_str or 'InterfaceError' in error_str or 'OperationalError' in error_str:
                # Determine process time even if failed
                process_time = time.perf_counter_ns() - start_time
                logger.error(
                    'request_failed_db_connection',
                    http_method=request.method,
                    url=str(request.url),
                    process_time_ms=process_time / 1_000_000,
                    exc_info=True,
                )
                from starlette.responses import JSONResponse

                return JSONResponse(
                    status_code=503,
                    content={'detail': 'Service Unavailable: Database connection failed. Please try again.'},
                )

            # Determine process time even if failed
            process_time = time.perf_counter_ns() - start_time
            logger.error(
                'request_failed',
                http_method=request.method,
                url=str(request.url),
                process_time_ms=process_time / 1_000_000,
                exc_info=True,
            )
            raise

        process_time = time.perf_counter_ns() - start_time
        status_code = response.status_code
        url = str(request.url)
        client_host = request.client.host if request.client else 'unknown'

        # Log at info level for success, error for 5xx, warn for 4xx
        log_method = logger.info
        if status_code >= 500:
            log_method = logger.error
        elif status_code >= 400:
            log_method = logger.warning

        log_method(
            'request_finished',
            http_method=request.method,
            url=url,
            status_code=status_code,
            process_time_ms=process_time / 1_000_000,
            client_ip=client_host,
        )

        return response
