"""Base class for services that are scoped to a specific owner/parent ID."""

import uuid
from typing import Any, TypeVar, overload

from pydantic import BaseModel
from rssa_storage.shared import BaseRepository, RepoQueryOptions

from .base_service import BaseService

ModelType = TypeVar('ModelType')
RepoType = TypeVar('RepoType', bound=BaseRepository)
SchemaType = TypeVar('SchemaType', bound=BaseModel)


class BaseScopedService(BaseService[ModelType, RepoType]):
    """Service that restricts access to a specific parent/owner ID."""

    scope_field: str

    @overload
    async def get(
        self,
        id: uuid.UUID,
        schema: type[SchemaType],
        *,
        owner_id: uuid.UUID | None = None,
        options: RepoQueryOptions | None = None,
    ) -> SchemaType | None: ...

    @overload
    async def get(
        self,
        id: uuid.UUID,
        schema: None = None,
        *,
        owner_id: uuid.UUID | None = None,
        options: RepoQueryOptions | None = None,
    ) -> ModelType | None: ...
    async def get(
        self,
        id: uuid.UUID,
        schema: type[SchemaType] | None = None,
        *,
        owner_id: uuid.UUID | None = None,  # Keyword-only scope enforcement
        options: RepoQueryOptions | None = None,
    ) -> Any | None:
        """Shadowed get: automatically applies owner scope."""
        options = options or RepoQueryOptions()
        if owner_id:
            options.filters[self.scope_field] = owner_id

        return await super().get(id, schema, options=options)

    @overload
    async def get_all(
        self, schema: type[SchemaType], *, owner_id: uuid.UUID | None = None, options: RepoQueryOptions
    ) -> list[SchemaType]: ...

    @overload
    async def get_all(
        self,
        schema: type[SchemaType],
        *,
        owner_id: uuid.UUID | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        search: str | None = None,
    ) -> list[SchemaType]: ...

    @overload
    async def get_all(
        self, schema: None = None, *, owner_id: uuid.UUID | None = None, options: RepoQueryOptions
    ) -> list[ModelType]: ...

    async def get_all(
        self,
        schema: type[SchemaType] | None = None,
        *,
        owner_id: uuid.UUID | None = None,
        options: RepoQueryOptions | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        search: str | None = None,
    ) -> list[Any]:
        """Shadowed get_all: automatically applies owner scope."""
        options = options or RepoQueryOptions()
        if owner_id:
            options.filters[self.scope_field] = owner_id

        return await super().get_all(
            schema, options=options, limit=limit, offset=offset, sort_by=sort_by, sort_dir=sort_dir, search=search
        )

    async def create(self, schema: BaseModel, *, owner_id: uuid.UUID | None = None, **kwargs) -> ModelType:
        """Shadowed create: automatically injects scope."""
        if owner_id:
            kwargs[self.scope_field] = owner_id
        return await super().create(schema, **kwargs)
