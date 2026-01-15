"""Dependency Factory for Database Sessions."""

from collections.abc import AsyncGenerator, Callable
from typing import Annotated, TypeVar

from fastapi import Depends
from rssa_storage.shared import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.services.base_service import BaseService

S = TypeVar('S', bound='BaseService')  # Generic service type
R = TypeVar('R', bound='BaseRepository')  # Generic repository type


class DependencyFactory:
    """Generates FastAPI dependencies bound to a specific Database Provider."""

    def __init__(self, db_provider: Callable[[], AsyncGenerator[AsyncSession, None]]):
        """Initialize the dependency factory with a database provider."""
        self.db_provider = db_provider

    def get_repository(self, repo_constructor: Callable[[AsyncSession], R]) -> Callable[[AsyncSession], R]:
        """Factory to create a dependency for a specific repository type."""

        def _get_repo(db: Annotated[AsyncSession, Depends(self.db_provider)]) -> R:
            return repo_constructor(db)

        return _get_repo

    def get_service(
        self, service_constructor: Callable[..., S], *repo_constructors: Callable[[AsyncSession], R]
    ) -> Callable[[AsyncSession], S]:
        """Composite Factory: Creates a Service by first creating its required Repositories."""

        def _get_service(db: Annotated[AsyncSession, Depends(self.db_provider)]) -> S:
            # Instantiate all required repos using the injected session
            repos = [repo_cls(db) for repo_cls in repo_constructors]
            return service_constructor(*repos)

        return _get_service
