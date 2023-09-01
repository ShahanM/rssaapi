from starlette.types import ASGIApp, Scope, Receive, Send


class ErrorHanlingMiddleware:
	def __init__(self, app: ASGIApp) -> None:
		self.app = app

	async def __call__(self, scope: Scope, receive: Receive, send: Send)\
		-> None:
		try:
			await self.app(scope, receive, send)
		except Exception as exc:
			raise
		finally:
			pass
