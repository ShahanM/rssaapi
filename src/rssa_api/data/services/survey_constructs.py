import uuid
from typing import Optional

from rssa_api.data.models.survey_constructs import SurveyConstruct
from rssa_api.data.repositories import (
    ConstructItemRepository,
    SurveyConstructRepository,
)
from rssa_api.data.schemas.base_schemas import PreviewSchema
from rssa_api.data.schemas.survey_constructs import (
    ConstructBaseSchema,
    SurveyConstructSchema,
)


class SurveyConstructService:
    def __init__(
        self,
        construct_repo: SurveyConstructRepository,
        item_repo: ConstructItemRepository,
    ):
        self.repo = construct_repo
        self.item_repo = item_repo

    async def create_survey_construct(
        self,
        new_construct: ConstructBaseSchema,
    ) -> SurveyConstruct:
        construct_to_insert = SurveyConstruct(name=new_construct.name, desc=new_construct.description)

        created_construct = await self.repo.create(construct_to_insert)

        return created_construct

    async def get_survey_constructs(
        self,
        limit: int,
        offset: int,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[PreviewSchema]:
        constructs = await self.repo.get_constructs_paginated(limit, offset, sort_by, sort_dir, search)
        construct_previews = [PreviewSchema.model_validate(construct) for construct in constructs]
        return construct_previews

    async def get_survey_construct(self, construct_id: uuid.UUID) -> SurveyConstruct:
        return await self.repo.get(construct_id)

    async def get_construct_summary(self, construct_id: uuid.UUID) -> Optional[SurveyConstructSchema]:
        # TODO: proposed feature => construct summary with usage statistics and response statistics
        construct_summary = await self.repo.get(construct_id)
        if not construct_summary:
            return None
        return SurveyConstructSchema.model_validate(construct_summary)

    async def get_construct_details(self, construct_id: uuid.UUID) -> Optional[SurveyConstructSchema]:
        survey_construct = await self.repo.get_detailed_construct_object(construct_id)
        if not survey_construct:
            return None
        return SurveyConstructSchema.model_validate(survey_construct)

    async def delete_survey_construct(self, construct_id: uuid.UUID) -> None:
        await self.repo.delete(construct_id)

    async def reorder_items(self, construct_id: uuid.UUID, items_map: dict) -> None:
        await self.item_repo.reorder_ordered_instances(construct_id, items_map)

    async def count_constructs(self, search: Optional[str] = None) -> int:
        return await self.repo.count_total_constructs(search)
