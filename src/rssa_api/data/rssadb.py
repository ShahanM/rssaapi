"""Asynchronous database session management for the RSSA Database."""

from rssa_api.data.db_base import BaseDatabaseContext, create_db_components, generic_get_db

# Initialize components specifically for the RSSA DB
async_engine, AsyncSessionLocal = create_db_components('RSSA_DB_NAME', echo=False)


class RSSADatabase(BaseDatabaseContext):
    """Asynchronous context manager for RSSA Database sessions."""

    def __init__(self):
        super().__init__(AsyncSessionLocal)


async def get_db():
    """Asynchronous generator to yield a database session."""
    async for session in generic_get_db(AsyncSessionLocal):
        yield session
