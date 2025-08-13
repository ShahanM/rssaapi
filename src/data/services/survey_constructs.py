import uuid

from data.models.survey_constructs import ConstructItem, SurveyConstruct
from data.repositories import (
	ConstructItemRepository,
	SurveyConstructRepository,
)
from data.schemas.survey_construct_schemas import SurveyConstructCreateSchema


class SurveyConstructService:
	def __init__(
		self,
		construct_repo: SurveyConstructRepository,
		item_repo: ConstructItemRepository,
	):
		self.construct_repo = construct_repo
		self.item_repo = item_repo

	async def create_survey_construct(
		self,
		new_construct: SurveyConstructCreateSchema,
	) -> SurveyConstruct:
		construct_to_insert = SurveyConstruct(name=new_construct.name, desc=new_construct.desc)

		created_construct = await self.construct_repo.create(construct_to_insert)

		return created_construct

	async def get_survey_constructs(self) -> list[SurveyConstruct]:
		return await self.construct_repo.get_all()

	async def get_survey_construct(self, construct_id: uuid.UUID) -> SurveyConstruct:
		return await self.construct_repo.get(construct_id)

	async def get_construct_summary(self, construct_id: uuid.UUID) -> SurveyConstruct:
		return await self.construct_repo.get_construct_summary(construct_id)

	async def get_construct_details(self, construct_id: uuid.UUID) -> SurveyConstruct:
		return await self.construct_repo.get_detailed_construct_object(construct_id)

	async def delete_survey_construct(self, construct_id: uuid.UUID) -> None:
		await self.construct_repo.delete(construct_id)

	async def reorder_items(self, construct_id: uuid.UUID, items_map: dict) -> None:
		await self.item_repo.reorder_ordered_instances(construct_id, items_map)
