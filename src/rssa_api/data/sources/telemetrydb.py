"""Asynchronous database session management for the Telemetry Database."""

from rssa_api.data.db_base import BaseDatabaseContext, create_db_components
from rssa_api.data.factory import DependencyFactory

async_engine, AsyncSessionLocal = create_db_components(
    'TELEMETRY_DB_NAME',
    use_neon_params=False,
    echo=False,
)


class TelemetryDatabase(BaseDatabaseContext):
    """Asynchronous context manager for Telemetry Database sessions."""

    def __init__(self):
        """Initialize the Telemetry Database context."""
        super().__init__(AsyncSessionLocal)


telemetry_db = TelemetryDatabase()
telemetry_deps = DependencyFactory(db_provider=telemetry_db)

get_repository = telemetry_deps.get_repository
get_service = telemetry_deps.get_service
