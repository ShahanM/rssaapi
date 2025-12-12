"""Base repository providing generic CRUD operations for SQLAlchemy models."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, Sequence, Type, TypeVar, Union, get_args

from sqlalchemy import Select, and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from rssa_api.data.models.rssa_base_models import DBBaseModel

ModelType = TypeVar('ModelType', bound=DBBaseModel)


@dataclass
class RepoQueryOptions:
    """Data class to encapsulate common query options for repositories."""

    ids: Optional[list[uuid.UUID]] = None
    filters: dict[str, Any] = field(default_factory=dict)
    search_text: Optional[str] = None
    search_columns: list[str] = field(default_factory=list)
    sort_by: Optional[str] = None
    sort_desc: bool = False
    limit: Optional[int] = None
    offset: Optional[int] = None
    include_deleted: bool = False
    load_options: Sequence[ExecutableOption] = field(default_factory=list)


class BaseRepository(Generic[ModelType]):
    """Base repository providing generic CRUD operations for SQLAlchemy models.

    Attributes:
        db (AsyncSession): The asynchronous database session.
        model (Type[ModelType]): The SQLAlchemy model class.
    """

    def __init__(self, db: AsyncSession, model: Optional[Type[ModelType]] = None):
        """Initialize the BaseRepository.

        Args:
            db: The asynchronous database session.
            model: The SQLAlchemy model class.
        """
        self.db = db

        if model:
            self.model = model
        else:
            inferred_model = self._infer_model_type()
            if inferred_model is None:
                raise ValueError(
                    f'Could not automatically infer ModelType for {self.__class__.__name__}. '
                    "Please pass the 'model' argument explicitly."
                )
            self.model = inferred_model

    def _infer_model_type(self) -> Union[Type[ModelType], None]:
        """Inspects the class hierarchy to find the generic type argument for ModelType."""
        cls = self.__class__
        for base in cls.__orig_bases__:  # type: ignore[attr-defined]
            origin = getattr(base, '__origin__', None)

            if origin is BaseRepository or (origin and issubclass(origin, BaseRepository)):
                args = get_args(base)

                if args and len(args) > 0:
                    return args[0]
        return None

    def _apply_query_options(self, query: Select, options: RepoQueryOptions) -> Select:
        """Centralized method to apply common query options to a SQLAlchemy Select query."""
        if options.ids:
            query = query.where(self.model.id.in_(options.ids))

        if options.filters:
            query = self._filter(query, options.filters)

        if options.search_text and options.search_columns:
            query = self._filter_similar(query, options.search_text, options.search_columns)

        if options.sort_by:
            query = self._sort(query, options.sort_by, options.sort_desc)

        if options.limit:
            query = query.limit(options.limit)

        if options.offset:
            query = query.offset(options.offset)

        if options.load_options:
            query = query.options(*options.load_options)

        if not options.include_deleted:
            query = self._apply_soft_delete(query)

        return query

    def _apply_soft_delete(self, query) -> Select:
        """Modify the query to exclude soft-deleted records.

        Args:
            query: The SQLAlchemy Select query to modify.

        Returns:
            The modified Select query excluding soft-deleted records.
        """
        # if hasattr(self.model, 'deleted_at'):
        deleted_attr = getattr(self.model, 'deleted_at', None)
        if deleted_attr is not None:
            query = query.where(deleted_attr.is_(None))
            # query = query.where(self.model.deleted_at.is_(None))
        return query

    async def find_many(self, options: Optional[RepoQueryOptions] = None) -> Sequence[ModelType]:
        """Find multiple instances based on the provided query options.

        Args:
            options: The query options to apply.

        Returns:
            A list of instances matching the query options.
        """
        options = options or RepoQueryOptions()
        query = select(self.model)
        query = self._apply_query_options(query, options)
        result = await self.db.execute(query)

        return result.scalars().all()

    async def find_one(self, options: Optional[RepoQueryOptions] = None) -> Optional[ModelType]:
        """Find a single instance based on the provided query options.

        Args:
            options: The query options to apply.

        Returns:
            An instance matching the query options, or None if not found.
        """
        options = options or RepoQueryOptions()
        query = select(self.model)
        query = self._apply_query_options(query, options)
        query = query.limit(1)
        result = await self.db.execute(query)
        return result.scalars().first()

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
        await self.db.flush()
        return instances

    async def update(self, instance_id: uuid.UUID, updated_fields: dict[str, Any]) -> Optional[ModelType]:
        """Update an instance in the database.

        Args:
            instance_id: The ID of the instance to update.
            updated_fields: A dictionary of fields to update.

        Returns:
            The updated instance or None if not found.
        """
        instance = await self.find_one(RepoQueryOptions(ids=[instance_id]))
        if instance:
            for field_name, value in updated_fields.items():
                setattr(instance, field_name, value)
            await self.db.flush()
            return instance
        return None

    async def delete(self, instance_id: uuid.UUID) -> bool:
        """Delete an instance from the database.

        Args:
            instance_id: The ID of the instance to delete.

        Returns:
            True if the instance was deleted, False otherwise.
        """
        instance = await self.find_one(RepoQueryOptions(ids=[instance_id]))
        if instance:
            if hasattr(instance, 'deleted_at'):
                from datetime import datetime, timezone

                instance.deleted_at = datetime.now(timezone.utc)
            else:
                await self.db.delete(instance)
            await self.db.flush()
            return True
        return False

    def _filter_similar(
        self,
        query: Select,
        filter_str: Optional[str] = None,
        filter_cols: Optional[list[str]] = None,
    ) -> Select:
        """Add search filters to the query based on specified columns.

        Args:
            query: The SQLAlchemy Select query to modify.
            filter_str: The search string to filter by.
            filter_cols: A list of column names to apply the search filter on.

        Returns:
            The modified Select query with search filters applied.
        """
        if filter_str and filter_cols:
            search_pattern = f'%{filter_str}%'
            conditions = []
            for col_name in filter_cols:
                column_attribute = getattr(self.model, col_name)
                conditions.append(column_attribute.ilike(search_pattern))
            return query.where(or_(*conditions))

        return query

    def _filter(
        self,
        query: Select,
        filters: dict[str, Any],
    ) -> Select:
        """Add exact match filters to the query based on specified columns.

        Args:
            query: The SQLAlchemy Select query to modify.
            filters: A list of tuples where each tuple contains a field name and its corresponding value.

        Returns:
            The modified Select query with exact match filters applied.
        """
        for col_name, col_val in filters.items():
            col_attr = getattr(self.model, col_name)
            if col_attr is not None:
                if isinstance(col_val, (list, tuple)):
                    query = query.where(col_attr.in_(col_val))
                else:
                    query = query.where(col_attr == col_val)

        return query

    def _sort(self, query: Select, sort_by: str, desc: bool = False) -> Select:
        """Sort the query by a specified column and direction.

        Args:
            query: The SQLAlchemy Select query to modify.
            sort_by: The column name to sort by.
            sort_dir: The direction of sorting ('asc' or 'desc').

        Returns:
            The modified Select query with sorting applied.
        """
        col_to_sort = getattr(self.model, sort_by, None)
        if col_to_sort is not None:
            if desc:
                query = query.order_by(col_to_sort.desc())
            else:
                query = query.order_by(col_to_sort.asc())
        return query

    async def count(
        self,
        filter_str: Optional[str] = None,
        filter_cols: Optional[list[str]] = None,
        filters: Optional[dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> int:
        """Count the total number of instances of the model.

        Returns:
            The total number of instances.
        """
        query = select(func.count()).select_from(self.model)
        if not include_deleted:
            query = self._apply_soft_delete(query)
        query = self._filter_similar(query, filter_str, filter_cols)
        query = self._filter(query, filters or {})

        result = await self.db.execute(query)
        return result.scalar_one()
