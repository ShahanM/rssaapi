import uuid
from typing import Optional

from data.models.survey_constructs import ConstructScale, ScaleLevel
from data.repositories import ConstructScaleRepository, ScaleLevelRepository
from data.schemas.base_schemas import PreviewSchema
from data.schemas.survey_constructs import ConstructScaleBaseSchema


class ConstructScaleService:
    def __init__(
        self,
        construct_scale_repo: ConstructScaleRepository,
        scale_level_repo: ScaleLevelRepository,
    ):
        self.repo = construct_scale_repo
        self.scale_level_repo = scale_level_repo

    async def create_construct_scale(self, create_scale: ConstructScaleBaseSchema, created_by: str) -> None:
        scale_name = create_scale.name or 'Unnamed Scale'
        scale_description = create_scale.description or ''

        scale_to_create = ConstructScale(
            name=scale_name,
            description=scale_description,
            created_by=created_by,
        )

        await self.repo.create(scale_to_create)

    async def get_construct_scales(
        self,
        limit: int,
        offset: int,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[PreviewSchema]:
        scales = await self.repo.get_scales_paginated(limit, offset, sort_by, sort_dir, search)
        scale_previews = [PreviewSchema.model_validate(scale) for scale in scales]
        return scale_previews

    async def get_construct_scale(self, scale_id: uuid.UUID) -> Optional[ConstructScale]:
        return await self.repo.get(scale_id)

    async def get_construct_scale_detail(self, scale_id: uuid.UUID) -> Optional[ConstructScale]:
        return await self.repo.get_details(scale_id)

    async def reorder_scale_levels(self, scale_id: uuid.UUID, levels_map: dict[uuid.UUID, int]) -> None:
        await self.scale_level_repo.reorder_ordered_instances(scale_id, levels_map)

    async def get_scale_levels(self, scale_id: uuid.UUID) -> list[ScaleLevel]:
        return await self.scale_level_repo.get_all_by_field('scale_id', scale_id)

    async def count_scales(self, search: Optional[str]) -> int:
        return await self.repo.count_total_scales(search)
