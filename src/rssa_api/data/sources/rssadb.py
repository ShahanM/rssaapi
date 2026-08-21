"""Asynchronous database session management for the RSSA Database."""

import rssa_api.core.config as cfg
from rssa_api.data.db_base import BaseDatabaseContext, create_db_components
from rssa_api.data.factory import DependencyFactory

is_development = cfg.get_env_var('ENV', 'production') == 'development'
async_engine, AsyncSessionLocal = create_db_components(
    'RSSA_DB_NAME',
    env_prefix='DB' if is_development else 'NEON',
    use_neon_params=not is_development,
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
get_scoped_service = deps.get_scoped_service
