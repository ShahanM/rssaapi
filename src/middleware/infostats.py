import time


class RequestHandlingStatsMiddleware:
	def __init__(self, app):
		self.app = app

	async def __call__(self, scope, receive, send):

		request_stats = {}
		
		start = time.time()

		request_stats = dict(scope)
		
		if scope["type"] != "http":
			await self.app(scope, receive, send)
			return

		body_size = 0

		async def receive_logging_request_body_size():
			nonlocal body_size

			message = await receive()
			assert message["type"] == "http.request"

			body_size += len(message.get("body", b""))

			if not message.get("more_body", False):
				request_stats["body_size"] = body_size

			if message:
				print(message)

			return message
		
		try:
			await self.app(scope, receive_logging_request_body_size, send)
		except Exception as exc:
			raise
		finally:
			end = time.time()
			elapsed = end - start

			request_stats["elapsed"] = elapsed
		
		# print(request_stats)
			