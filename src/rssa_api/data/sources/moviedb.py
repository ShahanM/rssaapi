"""Asynchronous database session management for the Movie Database."""

from rssa_api.data.db_base import BaseDatabaseContext, create_db_components
from rssa_api.data.factory import DependencyFactory

async_engine, AsyncSessionLocal = create_db_components(
    'MOVIE_DB_NAME',
    # env_prefix='NEON',
    use_neon_params=False,
    echo=True,
)


class MovieDatabase(BaseDatabaseContext):
    """Asynchronous context manager for Movie Database sessions."""

    def __init__(self):
        """Initialize."""
        super().__init__(AsyncSessionLocal)


movie_db = MovieDatabase()
movie_deps = DependencyFactory(db_provider=movie_db)

get_repository = movie_deps.get_repository
get_service = movie_deps.get_service
