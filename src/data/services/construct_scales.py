import uuid
from typing import Optional

from data.models.survey_constructs import ConstructScale, ScaleLevel
from data.repositories import ConstructScaleRepository, ScaleLevelRepository
from data.schemas.survey_construct_schemas import ConstructScaleCreateSchema


class ConstructScaleService:
	def __init__(
		self,
		construct_scale_repo: ConstructScaleRepository,
		scale_level_repo: ScaleLevelRepository,
	):
		self.construct_scale_repo = construct_scale_repo
		self.scale_level_repo = scale_level_repo

	async def create_construct_scale(self, create_scale: ConstructScaleCreateSchema, created_by: str) -> ConstructScale:
		scale_name = create_scale.name or 'Unnamed Scale'
		scale_description = create_scale.description or ''

		scale_to_create = ConstructScale(
			name=scale_name,
			description=scale_description,
			created_by=created_by,
		)

		return await self.construct_scale_repo.create(scale_to_create)

	async def get_construct_scales(self) -> list[ConstructScale]:
		return await self.construct_scale_repo.get_all()

	async def get_construct_scale(self, scale_id: uuid.UUID) -> Optional[ConstructScale]:
		return await self.construct_scale_repo.get(scale_id)

	async def get_construct_scale_detail(self, scale_id: uuid.UUID) -> Optional[ConstructScale]:
		return await self.construct_scale_repo.get_details(scale_id)

	async def reorder_scale_levels(self, scale_id: uuid.UUID, levels_map: dict[uuid.UUID, int]) -> None:
		await self.scale_level_repo.reorder_ordered_instances(scale_id, levels_map)

	async def get_scale_levels(self, scale_id: uuid.UUID) -> list[ScaleLevel]:
		return await self.scale_level_repo.get_all_by_field('scale_id', scale_id)
