"""Asynchronous database session management for the RSSA Database."""

from rssa_api.data.db_base import BaseDatabaseContext, create_db_components, generic_get_db
from rssa_api.data.factory import DependencyFactory

# Initialize components specifically for the RSSA DB
async_engine, AsyncSessionLocal = create_db_components('RSSA_DB_NAME', echo=False)


class RSSADatabase(BaseDatabaseContext):
    """Asynchronous context manager for RSSA Database sessions."""

    def __init__(self):
        super().__init__(AsyncSessionLocal)


# 1. Create the Database Dependency Instance
# This object is callable and yields a session (replaces 'get_db')
rssa_db = RSSADatabase()

# 2. Create the Dependency Factory bound to this DB
deps = DependencyFactory(db_provider=rssa_db)

# 3. Expose the helpers
get_repository = deps.get_repository
get_service = deps.get_service
# async def get_db():
#     """Asynchronous generator to yield a database session."""
#     async for session in generic_get_db(AsyncSessionLocal):
#         yield session
