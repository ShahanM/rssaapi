"""Base class for services that are scoped to a specific owner/parent ID."""

import uuid
from collections.abc import Sequence
from typing import Any, TypeVar, overload

from pydantic import BaseModel
from rssa_storage.shared import BaseRepository, RepoQueryOptions
from sqlalchemy.sql.base import ExecutableOption

from .base_service import BaseService

ModelType = TypeVar('ModelType')
RepoType = TypeVar('RepoType', bound=BaseRepository)
SchemaType = TypeVar('SchemaType', bound=BaseModel)


class BaseScopedService(BaseService[ModelType, RepoType]):
    """Service that restricts access to a specific parent/owner ID."""

    scope_field: str

    @overload
    async def get_for_owner(
        self,
        owner_id: uuid.UUID,
        item_id: uuid.UUID,
        schema: type[SchemaType],
        options: Sequence[ExecutableOption] | None = None,
    ) -> SchemaType | None: ...

    @overload
    async def get_for_owner(
        self,
        owner_id: uuid.UUID,
        item_id: uuid.UUID,
        schema: None = None,
        options: Sequence[ExecutableOption] | None = None,
    ) -> ModelType | None: ...

    async def get_for_owner(
        self,
        owner_id: uuid.UUID,
        item_id: uuid.UUID,
        schema: type[SchemaType] | None = None,
        options: Sequence[ExecutableOption] | None = None,
    ) -> Any | None:
        """Get an item, but ONLY if it belongs to the owner."""
        repo_options = RepoQueryOptions(
            filters={'id': item_id},
            load_options=options or [],
        )
        item = await self.repo.find_one(repo_options)

        if not item:
            return None

        if getattr(item, self.scope_field) != owner_id:
            return None

        if schema:
            return schema.model_validate(item)

        return item

    async def get_paged_for_owner(
        self,
        owner_id: uuid.UUID,
        limit: int,
        offset: int,
        schema: type[SchemaType] | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        search: str | None = None,
    ) -> list[Any]:
        """Fetch list explicitly scoped to the owner."""
        scope_filter = {self.scope_field: owner_id}

        search_cols = getattr(self.repo, 'SEARCHABLE_COLUMNS', [])

        repo_options = RepoQueryOptions(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=(sort_dir == 'desc') if sort_dir else False,
            search_text=search,
            search_columns=search_cols,
            filters=scope_filter,
        )
        items = await self.repo.find_many(repo_options)

        if not schema:
            return list(items)
        return [schema.model_validate(item) for item in items]

    async def create_for_owner(self, owner_id: uuid.UUID, schema: BaseModel, **kwargs) -> ModelType:
        """Create item and automatically inject the owner ID."""
        kwargs.update({self.scope_field: owner_id})
        return await self.create(schema, **kwargs)

    async def count_for_owner(self, owner_id: uuid.UUID, search: str | None = None) -> int:
        """Count items explicitly scoped to the owner."""
        scope_filter = {self.scope_field: owner_id}
        search_cols = getattr(self.repo, 'SEARCHABLE_COLUMNS', [])

        return await self.repo.count(
            filter_str=search,
            filter_cols=search_cols,
            filters=scope_filter,
        )

    async def get_all_for_owner(
        self,
        owner_id: uuid.UUID,
        schema: type[SchemaType] | None = None,
    ) -> list[Any]:
        """Get all items for a specific owner."""
        repo_options = RepoQueryOptions(filters={self.scope_field: owner_id})
        items = await self.repo.find_many(repo_options)
        if not schema:
            return list(items)
        return [schema.model_validate(item) for item in items]
