"""Dependency Factory for Database Sessions."""

import uuid
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Annotated, TypeVar

from fastapi import Depends, HTTPException, Request
from rssa_storage.shared import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from rssa_api.data.services.base_service import BaseService
S = TypeVar('S', bound='BaseService')
R = TypeVar('R', bound='BaseRepository')


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
            repos = [repo_cls(db) for repo_cls in repo_constructors]
            return service_constructor(*repos)

        return _get_service

    def get_scoped_service(
        self,
        service_constructor: Callable[..., S],
        scope_param_name: str,
        *repo_constructors: Callable[[AsyncSession], R],
    ) -> Callable:
        """Composite Factory for Scoped Services.

        Dynamically extracts the owner ID from the request path.
        """

        def _get_scoped_service(
            request: Request,
            db: Annotated[AsyncSession, Depends(self.db_provider)],
        ) -> S:
            raw_id = request.path_params.get(scope_param_name) or request.query_params.get(scope_param_name)

            if not raw_id:
                raise ValueError(
                    f"Scope parameter '{scope_param_name}' missing. "
                    f'Must be provided in the URL path or as a query parameter.'
                )

            try:
                owner_uuid = uuid.UUID(raw_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f'Invalid UUID for {scope_param_name}: {raw_id}'
                ) from ValueError

            repos = [repo_cls(db) for repo_cls in repo_constructors]
            return service_constructor(*repos, owner_id=owner_uuid)

        return _get_scoped_service
