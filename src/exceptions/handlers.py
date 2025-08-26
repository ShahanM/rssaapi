import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


async def integrity_error_handler(request: Request, exc: IntegrityError):
	logger.error(f'IntegrityError: {exc.orig}')
	return JSONResponse(
		status_code=status.HTTP_400_BAD_REQUEST,
		content={'detail': 'A data integrity error occurred.'},
	)


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
	logger.exception(f'SQLAlchemyError occurred: {exc}')
	return JSONResponse(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		content={'detail': 'An unexpected database error occurred.'},
	)


async def general_exception_handler(request: Request, exc: Exception):
	logger.exception(f'An unhandled exception occurred: {exc}')
	return JSONResponse(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		content={'detail': 'An unexpected server error occurred.'},
	)


# Helper function register all global excpetion handlers
def register_global_exception_handlers(app_instance: FastAPI):
	app_instance.exception_handler(IntegrityError)(integrity_error_handler)
	app_instance.exception_handler(SQLAlchemyError)(sqlalchemy_error_handler)
	app_instance.exception_handler(Exception)(general_exception_handler)
