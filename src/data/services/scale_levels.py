import uuid

from data.models.survey_constructs import ScaleLevel
from data.repositories import ScaleLevelRepository
from data.schemas.survey_constructs import ScaleLevelBaseSchema


class ScaleLevelService:
	def __init__(
		self,
		scale_level_repo: ScaleLevelRepository,
	):
		self.scale_level_repo = scale_level_repo

	async def create_scale_level(self, scale_id: uuid.UUID, create_scale_level: ScaleLevelBaseSchema) -> ScaleLevel:
		last_level = await self.scale_level_repo.get_last_ordered_instance(scale_id)
		order_position = last_level.order_position + 1 if last_level else 1

		new_scale = ScaleLevel(
			scale_id=scale_id,
			order_position=order_position,
			value=create_scale_level.value,
			label=create_scale_level.label,
		)

		await self.scale_level_repo.create(new_scale)

		return new_scale

	async def delete_scale_level(self, level_id: uuid.UUID) -> None:
		await self.scale_level_repo.delete_ordered_instance(level_id)
