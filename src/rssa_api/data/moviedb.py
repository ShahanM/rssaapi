"""Asynchronous database session management for the Movie Database."""

from rssa_api.data.db_base import BaseDatabaseContext, create_db_components, generic_get_db

# Initialize components specifically for the Movie DB
async_engine, AsyncSessionLocal = create_db_components('MOVIE_DB_NAME')


class MovieDatabase(BaseDatabaseContext):
    """Asynchronous context manager for Movie Database sessions."""

    def __init__(self):
        super().__init__(AsyncSessionLocal)


async def get_db():
    """Asynchronous generator to yield a database session."""
    async for session in generic_get_db(AsyncSessionLocal):
        yield session
