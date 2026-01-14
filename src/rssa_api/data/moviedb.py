"""Asynchronous database session management for the Movie Database."""

from rssa_api.data.db_base import BaseDatabaseContext, create_db_components
from rssa_api.data.factory import DependencyFactory

# Initialize components specifically for the Movie DB
async_engine, AsyncSessionLocal = create_db_components('MOVIE_DB_NAME')


class MovieDatabase(BaseDatabaseContext):
    """Asynchronous context manager for Movie Database sessions."""

    def __init__(self):
        super().__init__(AsyncSessionLocal)


movie_db = MovieDatabase()
movie_deps = DependencyFactory(db_provider=movie_db)

get_repository = movie_deps.get_repository
get_service = movie_deps.get_service


# async def get_db():
#     """Asynchronous generator to yield a database session."""
#     async for session in generic_get_db(AsyncSessionLocal):
#         yield session
