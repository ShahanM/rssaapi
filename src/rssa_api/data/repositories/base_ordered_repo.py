"""Base repository for ordered models."""

import uuid
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Type, TypeVar, Union

from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.rssa_base_models import DBBaseOrderedModel

from .base_repo import BaseRepository, RepoQueryOptions

ModelType = TypeVar('ModelType', bound=DBBaseOrderedModel)

@dataclass
class OrderedRepoQueryOptions(RepoQueryOptions):
    """Query options for ordered repositories."""
    min_order_position: Optional[int] = None


class BaseOrderedRepository(BaseRepository[ModelType]):
    """Base repository for ordered models."""

    parent_id_column_name: str

    def __init__(
        self,
        db: AsyncSession,
        model: Optional[Type[ModelType]] = None,
        parent_id_column_name: Optional[str] = None,
    ):
        """Initialize the BaseOrderedRepository.

        Args:
            db: The database session.
            model: The model class.
            parent_id_column_name: The name of the parent ID column in the model.
        """
        super().__init__(db, model)

        if parent_id_column_name:
            self.parent_id_column_name = parent_id_column_name

        if not self.parent_id_column_name:
            raise ValueError(
                f"Repository '{self.__class__.__name__}' must define 'parent_id_column_name' "
                'as a class attribute or pass it to __init__.'
            )
        self.parent_id_column = getattr(self.model, self.parent_id_column_name, None)

        if self.parent_id_column is None:
            raise AttributeError(
                f"Model '{self.model.__name__}' does not have a column named '{self.parent_id_column_name}'."
            )

    def _apply_query_options(self, query: Select, options: RepoQueryOptions) -> Select:
        """Apply query options to the query.

        Args:
            query: The SQLAlchemy query.
            options: The query options.

        Returns:
            The modified query.
        """
        query = super()._apply_query_options(query, options)

        if isinstance(options, OrderedRepoQueryOptions):
            if options.min_order_position is not None:
                query = query.where(self.model.order_position > options.min_order_position)

        return query

    async def find_many(self, options: Optional[RepoQueryOptions] = None) -> Sequence[ModelType]:
        """Find many ordered instances based on query options.

        Args:
            options: Query options including filters, sorting, pagination, etc.

        Returns:
            A list of ordered instances.
        """
        if options is None:
            options = OrderedRepoQueryOptions()
        
        # Ensure we are using OrderedRepoQueryOptions if passed generic RepoQueryOptions but need ordered features?
        # Or just rely on the caller passing the right type. 
        # For find_many in OrderedRepo, we probably want default sorting.
        
        if options.filters and self.parent_id_column_name in options.filters:
            # This logic was in the previous version, let's keep it but it might be redundant if filters handle it.
            # Actually, the previous code popped it. Let's see.
            # It popped it to use `self.parent_id_column == parent_id`.
            # If we leave it in filters, `BaseRepository._filter` uses `getattr(self.model, col_name)`.
            # `self.parent_id_column_name` is the column name string.
            # So `BaseRepository._filter` should handle it correctly if the model has that attribute.
            # The previous code might have been doing it to ensure `self.parent_id_column` (the attribute) is used?
            # But `getattr(self.model, self.parent_id_column_name)` is exactly what `_filter` does.
            # So we might not need to pop it.
            pass

        options.sort_by = options.sort_by or 'order_position'
        options.sort_desc = options.sort_desc

        return await super().find_many(options)

    async def get_all_ordered_instances(
        self,
        parent_id: uuid.UUID,
        limit: Optional[int] = None,
        include_deleted: bool = False,
    ) -> Sequence[ModelType]:
        """Get all ordered instances for a given parent ID.

        Args:
            parent_id: The parent ID.
            limit: Optional limit on the number of instances to retrieve.
            include_deleted: Whether to include soft-deleted instances.

        Returns:
            A list of ordered instances.
        """
        options = OrderedRepoQueryOptions(
            filters={self.parent_id_column_name: parent_id},
            sort_by='order_position',
            sort_desc=False,
            limit=limit,
            include_deleted=include_deleted,
        )
        return await self.find_many(options)

    async def get_first_ordered_instance(
        self, 
        parent_id: uuid.UUID,
        load_options: Optional[Sequence[Any]] = None,
    ) -> Optional[ModelType]:
        """Get the first ordered instance for a given parent ID.

        Args:
            parent_id: The parent ID.
            load_options: Optional list of loading options.

        Returns:
            The first ordered instance or None if not found.
        """
        options = OrderedRepoQueryOptions(
            filters={self.parent_id_column_name: parent_id},
            sort_by='order_position',
            sort_desc=False,
            limit=1,
            load_options=load_options,
        )
        return await self.find_one(options)

    async def get_next_ordered_instance(self, current_instance: ModelType) -> Optional[ModelType]:
        """Get the next ordered instance after the current instance.

        Args:
            current_instance: The current ordered instance.

        Returns:
            The next ordered instance or None if not found.
        """
        parent_id = getattr(current_instance, self.parent_id_column_name)
        
        options = OrderedRepoQueryOptions(
            filters={self.parent_id_column_name: parent_id},
            min_order_position=current_instance.order_position,
            sort_by='order_position',
            sort_desc=False,
            limit=1
        )
        return await self.find_one(options)

    async def get_last_ordered_instance(self, parent_id: uuid.UUID) -> Union[ModelType, None]:
        """Get the last ordered instance for a given parent ID.

        Args:
            parent_id: The parent ID.

        Returns:
            The last ordered instance or None if not found.
        """
        options = RepoQueryOptions(
            filters={self.parent_id_column_name: parent_id},
            sort_by='order_position',
            sort_desc=True,
            limit=1,
        )
        return await self.find_one(options)

    async def delete_ordered_instance(self, instance_id: uuid.UUID) -> None:
        """Delete ordered instance and update order positions of subsequent instances.

        Args:
            instance_id: The ID of the instance to delete.

        Returns:
            None
        """
        # instance = await self.get(instance_id)
        instance = await self.find_one(RepoQueryOptions(filters={'id': instance_id}))

        if instance:
            deleted_position = instance.order_position
            parent_id = getattr(instance, self.parent_id_column_name)

            await self.delete(instance_id)

            update_stmt = (
                update(self.model)
                .where(self.parent_id_column == parent_id, self.model.order_position > deleted_position)
                .values(order_position=self.model.order_position - 1)
            )

            await self.db.execute(update_stmt)
            await self.db.flush()

    async def purge_ordered_instance(self, instance_id: uuid.UUID) -> None:
        """Purge ordered instance from the database (non-reversible).

        Args:
            instance_id: The ID of the instance to purge.

        Returns:
            None
        """
        # instance = await self.get(instance_id)
        instance = await self.find_one(RepoQueryOptions(filters={'id': instance_id}))

        if instance:
            deleted_position = instance.order_position
            parent_id = getattr(instance, self.parent_id_column_name)

            await self.db.delete(instance)

            update_stmt = (
                update(self.model)
                .where(self.parent_id_column == parent_id, self.model.order_position > deleted_position)
                .values(order_position=self.model.order_position - 1)
            )

            await self.db.execute(update_stmt)
            await self.db.flush()

    async def reorder_ordered_instances(self, parent_id: uuid.UUID, instances_map: dict[uuid.UUID, int]) -> None:
        """Reorder ordered instances based on the provided mapping.

        Args:
            parent_id: The parent ID.
            instances_map: A mapping of instance IDs to their new order positions.

        Returns:
            None
        """
        for instance_id, new_position in instances_map.items():
            stmt = (
                update(self.model)
                .where(self.model.id == instance_id, self.parent_id_column == parent_id)
                .values(order_position=new_position)
            )
            await self.db.execute(stmt)

        await self.db.flush()
