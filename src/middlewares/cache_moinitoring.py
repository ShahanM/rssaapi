import logging
import time

from starlette.requests import Request

CACHE_HITS = 0
TOTAL_REQUESTS = 0
LAST_LOG_TIME = time.time()
LOGGING_INTERVAL = 60
logger = logging.getLogger(__name__)


async def cache_monitoring_middleware(request: Request, call_next):
	global TOTAL_REQUESTS, CACHE_HITS, LAST_LOG_TIME
	TOTAL_REQUESTS += 1
	response = await call_next(request)

	current_time = time.time()
	if current_time - LAST_LOG_TIME >= LOGGING_INTERVAL:
		hit_rate = (CACHE_HITS / TOTAL_REQUESTS) * 100 if TOTAL_REQUESTS > 0 else 0
		logger.info(f'Cache Hit Rate: {hit_rate:.2f}% (Hits: {CACHE_HITS}, Total: {TOTAL_REQUESTS})')
		CACHE_HITS = 0
		TOTAL_REQUESTS = 0
		LAST_LOG_TIME = current_time

	return response
