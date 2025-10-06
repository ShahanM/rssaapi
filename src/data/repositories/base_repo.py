import uuid
from typing import Any, Generic, Optional, Sequence, Type, TypeVar, Union

from sqlalchemy import Select, and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.rssa_base_models import DBBaseModel

ModelType = TypeVar('ModelType', bound=DBBaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def create(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def create_all(self, instances: list[ModelType]) -> list[ModelType]:
        self.db.add_all(instances)
        return instances

    async def get(self, instance_id: uuid.UUID) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == instance_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self) -> list[ModelType]:
        query = select(self.model)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_from_ids(self, instance_ids: list[uuid.UUID]) -> Optional[list[ModelType]]:
        query = select(self.model).where(self.model.id.in_(instance_ids))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, id: uuid.UUID, update_data: dict) -> Optional[ModelType]:
        instance = await self.get(id)
        if instance:
            for key, value in update_data.items():
                setattr(instance, key, value)
            await self.db.flush()
            return instance
        return None

    async def delete(self, instance_id: uuid.UUID) -> bool:
        """Performs a soft delete by adding a deleted_at timestamp."""
        deleted_instance = await self.update(instance_id, {'deleted_at': func.now()})

        return deleted_instance is not None

    async def purge(self, instance_id: uuid.UUID) -> bool:
        """Deletes instance from the database (non-reversible)."""
        query = delete(self.model).where(self.model.id == instance_id)
        result = await self.db.execute(query)
        await self.db.flush()

        return result.rowcount > 0

    async def get_by_field(self, field_name: str, value: Any) -> Union[ModelType, None]:
        column_attribute = getattr(self.model, field_name, None)
        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        query = select(self.model).where(column_attribute == value)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_fields(self, filters: list[tuple[str, Any]]) -> Optional[ModelType]:
        _filter_criteria = []
        for col_name, col_value in filters:
            column_attribute = getattr(self.model, col_name)
            _filter_criteria.append(column_attribute == col_value)
        query = select(self.model).where(and_(*_filter_criteria))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all_by_field(self, field_name: str, value: Any) -> list[ModelType]:
        column_attribute = getattr(self.model, field_name, None)
        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}" to query by.')

        query = select(self.model).where(column_attribute == value)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_by_fields(self, filters: list[tuple[str, Any]]) -> Sequence[ModelType]:
        _filter_criteria = []
        for col_name, col_value in filters:
            column_attribute = getattr(self.model, col_name)
            _filter_criteria.append(column_attribute == col_value)
        query = select(self.model).where(and_(*_filter_criteria))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_by_field_in_values(self, field_name: str, values: list[Any]) -> list[ModelType]:
        column_attribute = getattr(self.model, field_name, None)

        if column_attribute is None:
            raise AttributeError(f'Model "{self.model.__name__}" has no attribute "{field_name}"" to query by.')

        if not values:
            return []

        query = select(self.model).where(column_attribute.in_(values))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _add_search_filter(self, query: Select, search: Union[str, None], search_cols: list[str]) -> Select:
        if search:
            search_pattern = f'%{search}%'
            conditions = []
            for col_name in search_cols:
                column_attribute = getattr(self.model, col_name)
                conditions.append(column_attribute.ilike(search_pattern))
            return query.where(or_(*conditions))
        return query

    def _sort_by_column(self, query: Select, sort_by: Optional[str], sort_dir: Optional[str]) -> Select:
        if sort_by:
            column_to_sort = getattr(self.model, sort_by, None)
            if column_to_sort is not None:
                if sort_dir and sort_dir.lower() == 'desc':
                    query = query.order_by(column_to_sort.desc())
                else:
                    query = query.order_by(column_to_sort.asc())
        return query
