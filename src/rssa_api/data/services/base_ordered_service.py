"""Service for models that have an inherent order."""

import uuid
from typing import Any, Optional, Type, TypeVar, overload

from pydantic import BaseModel

from rssa_api.data.repositories.base_ordered_repo import BaseOrderedRepository
from rssa_api.data.services.base_scoped_service import BaseScopedService

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

    async def create_for_owner(self, owner_id: uuid.UUID, schema: BaseModel, **kwargs) -> OrderedModelType:
        """Overrides the generic scoped create to add Ordering Logic.

        Here, 'owner_id' acts as the 'parent_id'.

        Args:
            owner_id: The ID of the owner/parent entity.
            schema: The Pydantic schema used to create the new item.
            **kwargs: Additional keyword arguments to pass to the creation method.

        Returns:
            The created ordered model instance.
        """
        last_item = await self.repo.get_last_ordered_instance(owner_id)
        next_pos = last_item.order_position + 1 if last_item else 1

        kwargs['order_position'] = next_pos

        return await super().create_for_owner(owner_id, schema, **kwargs)

    async def reorder_items(self, parent_id: uuid.UUID, items_map: dict[uuid.UUID, int]) -> None:
        """Reorder items under a specific parent.

        Args:
                parent_id: The ID of the parent entity.
                items_map: A mapping of item IDs to their new order positions.
        """
        await self.repo.reorder_ordered_instances(parent_id, items_map)

    @overload
    async def get_items_for_owner_as_ordered_list(
        self,
        owner_id: uuid.UUID,
        schema: Type[SchemaType],
        limit: Optional[int] = None,
    ) -> list[SchemaType]: ...

    @overload
    async def get_items_for_owner_as_ordered_list(
        self,
        owner_id: uuid.UUID,
        schema: None = None,
        limit: Optional[int] = None,
    ) -> list[OrderedModelType]: ...

    async def get_items_for_owner_as_ordered_list(
        self,
        owner_id: uuid.UUID,
        schema: Optional[Type[SchemaType]] = None,
        limit: Optional[int] = None,
    ) -> list[Any]:
        """Get all items for a specific owner as an ordered list.

        Args:
            owner_id: The ID of the owner/parent entity.
            limit: Optional limit on the number of items to retrieve.
            schema: Optional Pydantic schema to validate each item against.

        Returns:
            A list of ordered items, optionally validated against the schema.
        """
        ordered_items = await self.repo.get_all_ordered_instances(owner_id, limit=limit)

        if schema:
            return [schema.model_validate(item) for item in ordered_items]

        return list(ordered_items)
