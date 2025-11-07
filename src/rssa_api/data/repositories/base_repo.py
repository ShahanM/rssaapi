"""Base repository providing generic CRUD operations for SQLAlchemy models."""

import uuid
from typing import Any, Generic, Optional, Sequence, Type, TypeVar, Union

from sqlalchemy import Select, and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.rssa_base_models import DBBaseModel

ModelType = TypeVar('ModelType', bound=DBBaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository providing generic CRUD operations for SQLAlchemy models.

    Attributes:
        db (AsyncSession): The asynchronous database session.
        model (Type[ModelType]): The SQLAlchemy model class.
    """

    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        """Initialize the BaseRepository.

        Args:
            db: The asynchronous database session.
            model: The SQLAlchemy model class.
        """
        self.db = db
        self.model = model

    async def create(self, instance: ModelType) -> ModelType:
        """Create a new instance in the database.

        Args:
            instance: The instance to create.

        Returns:
            The created instance.
        """
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def create_all(self, instances: list[ModelType]) -> list[ModelType]:
        """Create multiple instances in the database.

        Args:
            instances: A list of instances to create.

        Returns:
            The list of created instances.
        """
        self.db.add_all(instances)
        return instances

    async def get(self, instance_id: uuid.UUID) -> Optional[ModelType]:
        """Get an instance by its ID.

        Args:
            instance_id: The UUID of the instance to retrieve.

        Returns:
            The instance if found, else None.
        """
        query = select(self.model).where(self.model.id == instance_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self) -> list[ModelType]:
        """Get all instances of the model.

        Returns:
            A list of all instances.
        """
        query = select(self.model)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_from_ids(self, instance_ids: list[uuid.UUID]) -> Optional[list[ModelType]]:
        """Get all instances matching the provided list of IDs.

        Args:
            instance_ids: A list of UUIDs of the instances to retrieve.

        Returns:
            A list of instances matching the IDs.
        """
        query = select(self.model).where(self.model.id.in_(instance_ids))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, id: uuid.UUID, update_data: dict) -> Optional[ModelType]:
        """Update an instance with the provided data.

        Args:
            id: The UUID of the instance to update.
            update_data: A dictionary of fields to update with their new values.

        Returns:
            The updated instance if found, else None.
        """
        instance = await self.get(id)
        if instance:
            for key, value in update_data.items():
                setattr(instance, key, value)
            await self.db.flush()
            return instance
        return None

    async def delete(self, instance_id: uuid.UUID) -> bool:
        """Performs a soft delete by adding a deleted_at timestamp.

        Args:
            instance_id: The UUID of the instance to delete.

        Returns:
            True if the instance was found and marked as deleted, else False.
        """
        deleted_instance = await self.update(instance_id, {'deleted_at': func.now()})

        return deleted_instance is not None

    async def purge(self, instance_id: uuid.UUID) -> bool:
        """Deletes instance from the database (non-reversible).

        Args:
            instance_id: The UUID of the instance to purge.

        Returns:
            True if the instance was found and deleted, else False.
        """
        query = delete(self.model).where(self.model.id == instance_id)
        result = await self.db.execute(query)
        await self.db.flush()

        return result.rowcount > 0  # type: ignore

    async def get_by_field(self, field_name: str, value: Any) -> Union[ModelType, None]:
        """Get an instance by a specific field.

        Args:
            field_name: The name of the field to filter by.
            value: The value of the field to match.

        Returns:
            The instance if found, else None.
        """
        column_attribute = getattr(self.model, field_name, None)
        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        query = select(self.model).where(column_attribute == value)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_fields(self, filters: list[tuple[str, Any]]) -> Optional[ModelType]:
        """Get an instance by multiple fields.

        Args:
            filters: A list of tuples where each tuple contains a field name and its corresponding value.

        Returns:
            The instance if found, else None.
        """
        _filter_criteria = []
        for col_name, col_value in filters:
            column_attribute = getattr(self.model, col_name)
            _filter_criteria.append(column_attribute == col_value)
        query = select(self.model).where(and_(*_filter_criteria))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all_by_field(self, field_name: str, value: Any) -> list[ModelType]:
        """Get all instances matching a specific field value.

        Args:
            field_name: The name of the field to filter by.
            value: The value of the field to match.

        Returns:
            A list of instances matching the field value.
        """
        column_attribute = getattr(self.model, field_name, None)
        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        query = select(self.model).where(column_attribute == value)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_by_fields(self, filters: list[tuple[str, Any]]) -> Sequence[ModelType]:
        """Get all instances matching multiple field values.

        Args:
            filters: A list of tuples where each tuple contains a field name and its corresponding value.

        Returns:
            A list of instances matching the field values.
        """
        _filter_criteria = []
        for col_name, col_value in filters:
            column_attribute = getattr(self.model, col_name)
            _filter_criteria.append(column_attribute == col_value)
        query = select(self.model).where(and_(*_filter_criteria))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_by_field_in_values(self, field_name: str, values: list[Any]) -> list[ModelType]:
        """Get all instances where a specific field's value is in a list of values.

        Args:
            field_name: The name of the field to filter by.
            values: A list of values to match against the field.

        Returns:
            A list of instances matching the field values.
        """
        column_attribute = getattr(self.model, field_name, None)

        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}"" to query by.')

        if not values:
            return []

        query = select(self.model).where(column_attribute.in_(values))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _add_search_filter(self, query: Select, search: Union[str, None], search_cols: list[str]) -> Select:
        """Add search filters to the query based on specified columns.

        Args:
            query: The SQLAlchemy Select query to modify.
            search: The search string to filter by.
            search_cols: A list of column names to apply the search filter on.

        Returns:
            The modified Select query with search filters applied.
        """
        if search:
            search_pattern = f'%{search}%'
            conditions = []
            for col_name in search_cols:
                column_attribute = getattr(self.model, col_name)
                conditions.append(column_attribute.ilike(search_pattern))
            return query.where(or_(*conditions))
        return query

    def _sort_by_column(self, query: Select, sort_by: Optional[str], sort_dir: Optional[str]) -> Select:
        """Sort the query by a specified column and direction.

        Args:
            query: The SQLAlchemy Select query to modify.
            sort_by: The column name to sort by.
            sort_dir: The direction of sorting ('asc' or 'desc').

        Returns:
            The modified Select query with sorting applied.
        """
        if sort_by:
            column_to_sort = getattr(self.model, sort_by, None)
            if column_to_sort is not None:
                if sort_dir and sort_dir.lower() == 'desc':
                    query = query.order_by(column_to_sort.desc())
                else:
                    query = query.order_by(column_to_sort.asc())
        return query
