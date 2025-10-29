import uuid
from typing import Optional, Type, TypeVar, Union

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.rssa_base_models import DBBaseOrderedModel

from .base_repo import BaseRepository

ModelType = TypeVar('ModelType', bound=DBBaseOrderedModel)


class BaseOrderedRepository(BaseRepository[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType], parent_id_column_name: str):
        super().__init__(db, model)
        self.parent_id_column_name = parent_id_column_name
        self.parent_id_column = getattr(self.model, parent_id_column_name, None)
        if self.parent_id_column is None:
            raise AttributeError(
                f"Model '{self.model.__name__}' does not have a column named '{self.parent_id_column_name}'."
            )

    async def get_first_ordered_instance(self, parent_id: uuid.UUID) -> Union[ModelType, None]:
        query = select(self.model).where(self.parent_id_column == parent_id).order_by(self.model.order_position)
        result = await self.db.execute(query)

        return result.scalars().first()

    async def get_next_ordered_instance(self, current_instance: ModelType, full_entity=False) -> Optional[ModelType]:
        query = select(self.model)
        query = (
            query.where(self.parent_id_column == getattr(current_instance, self.parent_id_column_name))
            .where(self.model.order_position > current_instance.order_position)
            .order_by(self.model.order_position.asc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_last_ordered_instance(self, parent_id: uuid.UUID) -> Union[ModelType, None]:
        query = select(self.model).where(self.parent_id_column == parent_id).order_by(self.model.order_position.desc())
        result = await self.db.execute(query)

        return result.scalars().first()

    async def delete_ordered_instance(self, instance_id: uuid.UUID) -> None:
        instance = await self.get(instance_id)

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
        instance = await self.get(instance_id)

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
        for instance_id, new_position in instances_map.items():
            stmt = (
                update(self.model)
                .where(self.model.id == instance_id, self.parent_id_column == parent_id)
                .values(order_position=new_position)
            )
            await self.db.execute(stmt)

        await self.db.flush()
