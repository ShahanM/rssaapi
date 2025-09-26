import uuid
from typing import Optional

from data.models.study_components import Page
from data.repositories import PageContentRepository, PageRepository, StudyStepRepository
from data.schemas.study_components import PageBaseSchema, PageNavigationSchema


class StepPageService:
    def __init__(
        self,
        page_repo: PageRepository,
        content_repo: PageContentRepository,
        step_repo: StudyStepRepository,
    ):
        self.repo = page_repo
        self.content_repo = content_repo
        self.step_repo = step_repo

    async def create_step_page(self, study_id: uuid.UUID, step_id: uuid.UUID, new_page: PageBaseSchema) -> None:
        last_page = await self.repo.get_last_ordered_instance(step_id)
        next_order_pos = 1 if last_page is None else last_page.order_position + 1
        step_page = Page(
            study_id=study_id,
            step_id=step_id,
            order_position=next_order_pos,
            name=new_page.name,
            description=new_page.description,
            page_type=new_page.page_type,
        )

        await self.repo.create(step_page)

    async def get_pages_for_step(self, study_step_id: uuid.UUID) -> list[Page]:
        return await self.repo.get_all_by_field('step_id', study_step_id)

    async def get_step_page(self, page_id: uuid.UUID) -> Page:
        return await self.repo.get(page_id)

    async def get_page_with_content_detail(self, page_id: uuid.UUID) -> Page:
        return await self.repo.get_page_with_content_detail(page_id)

    async def get_page_with_navigation(self, page_id: uuid.UUID) -> Optional[PageNavigationSchema]:
        page = await self.get_page_with_content_detail(page_id)
        if not page:
            return None
        next_page_id = await self.repo.get_next_ordered_instance(page)
        if next_page_id is not None:
            page.next = next_page_id
        else:
            page.next = None

        return PageNavigationSchema.model_validate(page)

    async def get_first_page_with_navitation(self, step_id: uuid.UUID) -> Optional[PageNavigationSchema]:
        page = await self.repo.get_first_ordered_instance(step_id)
        if page is None:
            return None
        page_with_nav = await self.get_page_with_navigation(page.id)
        return PageNavigationSchema.model_validate(page_with_nav)

    async def get_first_page_in_step(self, step_id: uuid.UUID) -> Optional[Page]:
        return await self.repo.get_first_ordered_instance(step_id)

    async def update_step_page(self, page_id: uuid.UUID, updated_page: dict[str, str]) -> None:
        await self.repo.update(page_id, updated_page)

    async def delete_step_page(self, page_id: uuid.UUID) -> None:
        await self.repo.delete(page_id)
