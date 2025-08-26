import uuid

from data.models.survey_constructs import ConstructItem
from data.repositories import ConstructItemRepository
from data.schemas.survey_construct_schemas import ConstructItemCreateSchema


class ConstructItemService:
	def __init__(
		self,
		item_repo: ConstructItemRepository,
	):
		self.item_repo = item_repo

	async def get_construct_item(self, item_id: uuid.UUID) -> ConstructItem:
		return await self.item_repo.get(item_id)

	async def create_construct_item(self, new_item: ConstructItemCreateSchema) -> ConstructItem:
		last_item = await self.item_repo.get_last_ordered_instance(new_item.construct_id)
		order_position = last_item.order_position + 1 if last_item else 1

		item_to_create = ConstructItem(
			construct_id=new_item.construct_id,
			text=new_item.text,
			order_position=order_position,
		)

		await self.item_repo.create(item_to_create)

		return item_to_create

	async def delete_construct_item(self, item_id: uuid.UUID) -> None:
		await self.item_repo.delete_ordered_instance(item_id)
