import uuid
from typing import List

from data.models.survey_constructs import ConstructItem
from data.repositories.construct_item import ConstructItemRepository
from data.schemas.survey_construct_schemas import ConstructItemCreateSchema


class ConstructItemService:
	def __init__(self, construct_item_repo: ConstructItemRepository):
		self.item_repo = construct_item_repo

	async def get_construct_item(self, item_id: uuid.UUID) -> ConstructItem:
		return await self.item_repo.get(item_id)

	async def create_construct_item(self, new_item: ConstructItemCreateSchema) -> ConstructItem:
		item_to_create = ConstructItem(
			construct_id=new_item.construct_id,
			text=new_item.text,
			order_position=new_item.order_position,
			item_type=new_item.item_type,
		)

		await self.item_repo.create(item_to_create)

		return item_to_create
