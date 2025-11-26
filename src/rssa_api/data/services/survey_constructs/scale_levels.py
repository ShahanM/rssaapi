import uuid

from rssa_api.data.models.survey_constructs import SurveyScaleLevel
from rssa_api.data.repositories.survey_constructs import SurveyScaleLevelRepository
from rssa_api.data.schemas.survey_constructs import ScaleLevelBaseSchema


class SurveyScaleLevelService:
    def __init__(
        self,
        scale_level_repo: SurveyScaleLevelRepository,
    ):
        self.scale_level_repo = scale_level_repo

    async def create_scale_level(
        self, scale_id: uuid.UUID, create_scale_level: ScaleLevelBaseSchema
    ) -> SurveyScaleLevel:
        last_level = await self.scale_level_repo.get_last_ordered_instance(scale_id)
        order_position = last_level.order_position + 1 if last_level else 1

        new_scale = SurveyScaleLevel(
            scale_id=scale_id,
            order_position=order_position,
            value=create_scale_level.value,
            label=create_scale_level.label,
        )

        await self.scale_level_repo.create(new_scale)

        return new_scale

    async def delete_scale_level(self, level_id: uuid.UUID) -> None:
        await self.scale_level_repo.delete_ordered_instance(level_id)

    async def reorder_scale_levels(self, scale_id: uuid.UUID, levels_map: dict[uuid.UUID, int]) -> None:
        await self.scale_level_repo.reorder_ordered_instances(scale_id, levels_map)

    async def get_scale_levels(self, scale_id: uuid.UUID) -> list[SurveyScaleLevel]:
        return await self.scale_level_repo.get_all_by_field('scale_id', scale_id)
