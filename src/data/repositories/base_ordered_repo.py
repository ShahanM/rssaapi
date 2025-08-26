import uuid
from operator import attrgetter
from typing import Type, TypeVar, Union

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .base_repo import BaseModelWithUUID, BaseRepository


class OrderedModelMixin:
	__abstract__ = True
	order_position: Mapped[int] = mapped_column(nullable=False, index=True)


class BaseOrderedModelWithUUID(BaseModelWithUUID, OrderedModelMixin):
	__abstract__ = True


ModelType = TypeVar('ModelType', bound=BaseOrderedModelWithUUID)


class BaseOrderedRepository(BaseRepository[ModelType]):
	def __init__(self, db: AsyncSession, model: Type[ModelType], parent_id_column_name: str):
		super().__init__(db, model)
		self.parent_id_column_name = parent_id_column_name
		self.parent_id_column = getattr(self.model, parent_id_column_name, None)
		if self.parent_id_column is None:
			raise AttributeError(
				f"Model '{self.model.__name__}' does not have a column named '{self.parent_id_column_name}'."
			)

	async def get_last_ordered_instance(self, parent_id: uuid.UUID) -> Union[ModelType, None]:
		query = select(self.model).where(self.parent_id_column == parent_id).order_by(self.model.order_position.desc())
		result = await self.db.execute(query)

		return result.scalars().first()

	async def delete_ordered_instance(self, instance_id: uuid.UUID) -> None:
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
