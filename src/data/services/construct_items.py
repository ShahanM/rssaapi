import uuid

from data.models.survey_constructs import ConstructItem
from data.repositories import ConstructItemRepository
from data.schemas.base_schemas import OrderedTextListItem
from data.schemas.survey_constructs import ConstructItemBaseSchema


class ConstructItemService:
	def __init__(
		self,
		item_repo: ConstructItemRepository,
	):
		self.repo = item_repo

	async def get_construct_item(self, item_id: uuid.UUID) -> ConstructItem:
		return await self.repo.get(item_id)

	async def create_construct_item(self, construct_id: uuid.UUID, new_item: ConstructItemBaseSchema) -> None:
		last_item = await self.repo.get_last_ordered_instance(construct_id)
		order_position = last_item.order_position + 1 if last_item else 1

		item_to_create = ConstructItem(
			construct_id=new_item.construct_id,
			text=new_item.text,
			order_position=order_position,
		)

		await self.repo.create(item_to_create)

	async def delete_construct_item(self, item_id: uuid.UUID) -> None:
		await self.repo.delete_ordered_instance(item_id)

	async def get_item_by_construct_id(self, construct_id: uuid.UUID) -> list[OrderedTextListItem]:
		items = await self.repo.get_all_by_field('construct_id', construct_id)

		if items is None or len(items) == 0:
			return []

		return [OrderedTextListItem.model_validate(item) for item in items]
