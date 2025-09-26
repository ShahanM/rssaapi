import uuid

from data.models.study_components import PageContent
from data.repositories import PageContentRepository
from data.schemas.study_components import PageContentBaseSchema, PageContentSchema


class PageContentService:
    def __init__(self, content_repo: PageContentRepository):
        self.repo = content_repo

    async def get_content_detail_by_page_id(self, page_id: uuid.UUID) -> list[PageContentSchema]:
        content = await self.repo.get_detailed_content_by_page_id(page_id)
        if not content:
            return []
        return [PageContentSchema.model_validate(c) for c in content]

    async def create_page_content(self, page_id: uuid.UUID, new_content: PageContentBaseSchema) -> None:
        last_step = await self.repo.get_last_ordered_instance(page_id)
        next_order_pos = 1 if last_step is None else last_step.order_position + 1
        study_step = PageContent(
            page_id=page_id,
            construct_id=new_content.construct_id,
            scale_id=new_content.scale_id,
            order_position=next_order_pos,
        )
        await self.repo.create(study_step)
