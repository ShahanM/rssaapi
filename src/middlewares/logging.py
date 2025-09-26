import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
	def __init__(self, app):
		super().__init__(app)
		self.app = app
		self.cache_hits = 0
		self.total_requests = 0
		self.last_log_time = time.time()
		self.logging_interval = 60  # Seconds

	async def dispatch(self, request: Request, call_next):
		start_time = time.time()
		self.total_requests += 1
		cache_hit = False

		if request.url.path == '/prefviz/recommendation/':
			cache_key = (
				frozenset(await self.get_ratings_from_request(request)),
				getattr(request.state, 'user_condition_id', None),
				getattr(request.state, 'is_baseline', None),
				getattr(request.state, 'study_id_from_condition', None),  # Or just study_id if you prefer
			)
			if hasattr(request.app.state, 'CACHE') and cache_key in request.app.state.CACHE:
				self.cache_hits += 1
				cache_hit = True
				logger.info(f'Cache hit for key: {cache_key}')
				response = request.app.state.CACHE[cache_key]
			else:
				response = await call_next(request)
				if (
					response.status_code < 400
					and request.method == 'POST'
					and request.url.path == '/prefviz/recommendation/'
				):
					if (
						hasattr(request.app.state, 'CACHE')
						and hasattr(request.app.state, 'CACHE_LIMIT')
						and hasattr(request.app.state, 'queue')
					):
						if len(request.app.state.queue) >= request.app.state.CACHE_LIMIT:
							old_key = request.app.state.queue.pop(0)
							del request.app.state.CACHE[old_key]
						request.app.state.CACHE[cache_key] = response
						request.app.state.queue.append(cache_key)
		else:
			response = await call_next(request)

		process_time = time.time() - start_time
		logger.info(
			f'Method={request.method} Path={request.url.path} Status={response.status_code} '
			f'ProcessTime={process_time:.4f}s CacheHit={cache_hit}'
		)

		current_time = time.time()
		if current_time - self.last_log_time >= self.logging_interval:
			hit_rate = (self.cache_hits / self.total_requests) * 100 if self.total_requests > 0 else 0
			logger.info(
				f'Cache Monitoring - Hit Rate: {hit_rate:.2f}% (Hits: {self.cache_hits}, Total: {self.total_requests})'
			)
			self.cache_hits = 0
			self.total_requests = 0
			self.last_log_time = current_time

		return response

	async def get_ratings_from_request(self, request: Request) -> list:
		try:
			body = await request.json()
			ratings_data = body.get('ratings', [])
			ratings = [tuple(item.values()) for item in ratings_data]  # Convert to tuple for hashability
			return ratings
		except Exception:
			return []
