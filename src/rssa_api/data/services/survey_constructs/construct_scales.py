import uuid
from typing import Optional

from rssa_api.data.models.survey_constructs import SurveyScale
from rssa_api.data.repositories.survey_constructs import SurveyScaleRepository
from rssa_api.data.schemas.base_schemas import PreviewSchema
from rssa_api.data.schemas.survey_constructs import ConstructScaleBaseSchema


class SurveyScaleService:
    def __init__(
        self,
        scale_repo: SurveyScaleRepository,
    ):
        self.repo = scale_repo

    async def create_construct_scale(self, create_scale: ConstructScaleBaseSchema, created_by: str) -> None:
        scale_name = create_scale.name or 'Unnamed Scale'
        scale_description = create_scale.description or ''

        scale_to_create = SurveyScale(
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
        scales = await self.repo.get_paged(
            limit, offset, sort_by, sort_dir, search, SurveyScaleRepository.SEARCHABLE_COLUMNS
        )
        scale_previews = [PreviewSchema.model_validate(scale) for scale in scales]
        return scale_previews

    async def get_construct_scale(self, scale_id: uuid.UUID) -> Optional[SurveyScale]:
        return await self.repo.get(scale_id)

    async def get_construct_scale_detail(self, scale_id: uuid.UUID) -> Optional[SurveyScale]:
        return await self.repo.get(scale_id, options=SurveyScaleRepository.LOAD_FULL_DETAILS)

    async def count_scales(self, search: Optional[str]) -> int:
        return await self.repo.count(filter_str=search, filter_cols=SurveyScaleRepository.SEARCHABLE_COLUMNS)
