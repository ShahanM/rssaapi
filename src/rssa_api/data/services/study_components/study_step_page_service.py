"""Service layer for managing study step pages."""

import uuid
from typing import Optional

from rssa_api.data.models.study_components import StudyStepPage
from rssa_api.data.repositories.study_components import (
    StudyStepPageContentRepository,
    StudyStepPageRepository,
    StudyStepRepository,
)
from rssa_api.data.schemas.study_components import PageBaseSchema, PageNavigationSchema, PageSchema


class StudyStepPageService:
    """Service for managing study step pages."""

    def __init__(
        self,
        page_repo: StudyStepPageRepository,
        content_repo: StudyStepPageContentRepository,
        step_repo: StudyStepRepository,
    ):
        """Initializes the StepPageService with the necessary repositories.

        Args:
            page_repo: Repository for managing step pages.
            content_repo: Repository for managing page content.
            step_repo: Repository for managing study steps.
        """
        self.repo = page_repo
        self.content_repo = content_repo
        self.step_repo = step_repo

    async def create_step_page(self, study_id: uuid.UUID, step_id: uuid.UUID, new_page: PageBaseSchema) -> None:
        """Creates a new step page within a study step.

        Args:
            study_id: The ID of the study.
            step_id: The ID of the study step.
            new_page: The data for the new step page.
        """
        last_page = await self.repo.get_last_ordered_instance(step_id)
        next_order_pos = 1 if last_page is None else last_page.order_position + 1
        step_page = StudyStepPage(
            study_id=study_id,
            step_id=step_id,
            order_position=next_order_pos,
            name=new_page.name,
            description=new_page.description,
            page_type=new_page.page_type,
        )

        await self.repo.create(step_page)

    async def get_pages_for_step(self, study_step_id: uuid.UUID) -> list[StudyStepPage]:
        """Retrieves all step pages for a given study step.

        Args:
            study_step_id: The ID of the study step.

        Returns:
            A list of step pages associated with the study step.
        """
        return await self.repo.get_all_by_field('step_id', study_step_id)

    async def get_step_page(self, page_id: uuid.UUID) -> Optional[StudyStepPage]:
        """Retrieves a step page by its ID.

        Args:
            page_id: The ID of the step page.

        Returns:
            The step page if found, otherwise None.
        """
        return await self.repo.get(page_id)

    async def get_page_with_content_detail(self, page_id: uuid.UUID) -> Optional[StudyStepPage]:
        """Retrieves a step page along with its content details.

        Args:
            page_id: The ID of the step page.

        Returns:
            The step page with content details if found, otherwise None.
        """
        return await self.repo.get_page_with_content_detail(page_id)

    async def get_page_with_navigation(self, page_id: uuid.UUID) -> Optional[PageNavigationSchema]:
        """Retrieves a step page along with its navigation details.

        Args:
            page_id: The ID of the step page.

        Returns:
            The step page with navigation details if found, otherwise None.
        """
        page = await self.repo.get_page_with_content_detail(page_id)
        if not page:
            return None
        next_page = await self.repo.get_next_ordered_instance(page)
        page_dto = PageSchema.model_validate(page)
        next_page_id = next_page.id if next_page else None

        final_schema = PageNavigationSchema(**page_dto.model_dump(), next=next_page_id)

        return final_schema

    async def get_first_page_with_navigation(self, step_id: uuid.UUID) -> Optional[PageNavigationSchema]:
        """Retrieves the first step page of a study step along with its navigation details.

        Args:
            step_id: The ID of the study step.

        Returns:
            The first step page with navigation details if found, otherwise None.
        """
        page = await self.repo.get_first_ordered_instance(step_id)
        if page is None:
            return None
        page_with_nav = await self.get_page_with_navigation(page.id)
        return PageNavigationSchema.model_validate(page_with_nav)

    async def get_first_page_in_step(self, step_id: uuid.UUID) -> Optional[StudyStepPage]:
        """Retrieves the first step page in a given study step.

        Args:
            step_id: The ID of the study step.

        Returns:
            The first step page if found, otherwise None.
        """
        return await self.repo.get_first_ordered_instance(step_id)

    async def update_step_page(self, page_id: uuid.UUID, updated_page: dict[str, str]) -> None:
        """Updates a step page with new data.

        Args:
            page_id: The ID of the step page to update.
            updated_page: A dictionary containing the updated page data.
        """
        await self.repo.update(page_id, updated_page)

    async def delete_step_page(self, page_id: uuid.UUID) -> None:
        """Deletes a step page by its ID.

        Args:
            page_id: The ID of the step page to delete.
        """
        await self.repo.delete(page_id)
