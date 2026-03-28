"""Service for models that have an inherent order."""

import uuid
from typing import Any, TypeVar

from pydantic import BaseModel
from rssa_storage.shared import BaseOrderedRepository, OrderedRepoQueryOptions, RepoQueryOptions

from rssa_api.data.services.base_scoped_service import BaseScopedService
from rssa_api.data.utility import extract_load_strategies

OrderedModelType = TypeVar('OrderedModelType')
OrderedRepoType = TypeVar('OrderedRepoType', bound='BaseOrderedRepository')
SchemaType = TypeVar('SchemaType', bound=BaseModel)


class BaseOrderedService(BaseScopedService[OrderedModelType, OrderedRepoType]):
    """Service for models that have an inherent order."""

    def __init__(self, repo: OrderedRepoType):
        """Initialize the BaseOrderedService with the given repository.

        Args:
            repo: The repository instance to be used by the service.
        """
        super().__init__(repo)

        self.scope_field = self.repo.parent_id_column_name

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
        """Shadowed get_all: applies scope, orders items, and prevents lazy loads."""
        if not isinstance(options, OrderedRepoQueryOptions):
            options = OrderedRepoQueryOptions(**(options.__dict__ if options else {}))

        options.sort_by = options.sort_by or 'order_position'

        top_cols, _ = extract_load_strategies(schema) if schema else (None, None)
        if top_cols is not None:
            required = {'id', 'order_position', self.repo.parent_id_column_name}
            current_cols = options.load_columns or []
            options.load_columns = list(set(current_cols).union(top_cols).union(required))

        return await super().get_all(
            schema,
            owner_id=owner_id,
            options=options,
            limit=limit,
            offset=offset,
            sort_by=sort_by or 'order_position',  # Apply default ordering here
            sort_dir=sort_dir,
            search=search,
        )

    async def create(self, schema: BaseModel, *, owner_id: uuid.UUID | None = None, **kwargs) -> OrderedModelType:
        """Shadowed create: injects owner scope AND calculates order position."""
        if not owner_id:
            raise ValueError('owner_id is required to create an ordered item.')

        last_item = await self.repo.get_last_ordered_instance(owner_id)
        kwargs['order_position'] = last_item.order_position + 1 if last_item else 1

        return await super().create(schema, owner_id=owner_id, **kwargs)

    async def reorder_items(self, parent_id: uuid.UUID, items_map: dict[uuid.UUID, int]) -> None:
        """Reorder items under a specific parent.

        Args:
                parent_id: The ID of the parent entity.
                items_map: A mapping of item IDs to their new order positions.
        """
        await self.repo.reorder_ordered_instances(parent_id, items_map)
