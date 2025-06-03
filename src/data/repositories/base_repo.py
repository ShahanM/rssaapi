import uuid
from typing import Generic, List, Type, TypeVar, Union

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModelWithUUID(DeclarativeBase):
	__abstract__ = True
	id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


ModelType = TypeVar('ModelType', bound=BaseModelWithUUID)


class BaseRepository(Generic[ModelType]):
	def __init__(self, db: AsyncSession, model: Type[ModelType]):
		self.db = db
		self.model = model

	async def create(self, instance: ModelType) -> ModelType:
		self.db.add(instance)
		await self.db.flush()
		return instance

	async def create_all(self, instances: List[ModelType]) -> List[ModelType]:
		self.db.add_all(instances)
		return instances

	async def get(self, instance_id: uuid.UUID) -> Union[ModelType, None]:
		query = select(self.model).where(self.model.id == instance_id)
		result = await self.db.execute(query)
		return result.scalars().first()

	async def get_all(self) -> list[ModelType]:
		query = select(self.model)
		result = await self.db.execute(query)
		return list(result.scalars().all())

	async def get_all_from_ids(self, instance_ids: List[uuid.UUID]) -> Union[List[ModelType], None]:
		query = select(self.model).where(self.model.id.in_(instance_ids))
		result = await self.db.execute(query)
		return list(result.scalars().all())

	async def update(self, id: uuid.UUID, update_data: dict) -> Union[ModelType, None]:
		instance = await self.get(id)
		if instance:
			for key, value in update_data.items():
				setattr(instance, key, value)
			await self.db.flush()
			return instance
		return None

	async def delete(self, instance_id: uuid.UUID) -> bool:
		query = delete(self.model).where(self.model.id == instance_id)
		result = await self.db.execute(query)
		await self.db.flush()

		return result.rowcount > 0
