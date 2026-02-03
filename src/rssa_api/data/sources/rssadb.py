"""Asynchronous database session management for the RSSA Database."""

from rssa_api.data.db_base import BaseDatabaseContext, create_db_components
from rssa_api.data.factory import DependencyFactory

# Initialize components specifically for the RSSA DB
async_engine, AsyncSessionLocal = create_db_components(
    'RSSA_DB_NAME',
    use_neon_params=True,
    echo=False,
)


class RSSADatabase(BaseDatabaseContext):
    """Asynchronous context manager for RSSA Database sessions."""

    def __init__(self):
        """Initialize the RSSA Database context."""
        super().__init__(AsyncSessionLocal)


rssa_db = RSSADatabase()
deps = DependencyFactory(db_provider=rssa_db)
get_repository = deps.get_repository
get_service = deps.get_service
