"""Survey Construct Service Module.

This module defines the SurveyConstructService class, which provides methods to manage
"""

import uuid
from typing import Optional

from rssa_api.data.models.survey_constructs import SurveyConstruct
from rssa_api.data.repositories.survey_constructs import SurveyConstructRepository, SurveyItemRepository
from rssa_api.data.schemas.base_schemas import PreviewSchema
from rssa_api.data.schemas.survey_constructs import (
    ConstructBaseSchema,
    SurveyConstructSchema,
)


class SurveyConstructService:
    """Service for managing survey constructs.

    This service provides methods to create, retrieve, update, and delete survey constructs,
    as well as to manage construct items and their order.

    Attributes:
        repo: Repository for survey constructs.
        item_repo: Repository for construct items.

    Methods:
        create_survey_construct: Create a new survey construct.
        get_survey_constructs: Retrieve a list of survey constructs with pagination.
        get_survey_construct: Retrieve a specific survey construct by ID.
        get_construct_summary: Retrieve a summary of a survey construct.
        get_construct_details: Retrieve detailed information about a survey construct.
        delete_survey_construct: Delete a survey construct by ID.
        reorder_items: Reorder items within a survey construct.
        count_constructs: Count total survey constructs with optional search filter.
    """

    def __init__(
        self,
        construct_repo: SurveyConstructRepository,
    ):
        """Initialize the SurveyConstructService.

        Args:
            construct_repo: Repository for survey constructs.
            # item_repo: Repository for construct items.
        """
        self.repo = construct_repo

    async def create_survey_construct(
        self,
        new_construct: ConstructBaseSchema,
    ) -> SurveyConstruct:
        """Create a new survey construct.

        Args:
            new_construct: Data for the new survey construct.

        Returns:
            The created SurveyConstruct object.
        """
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
        """Retrieve a list of survey constructs with pagination.

        Args:
            limit: Maximum number of constructs to retrieve.
            offset: Number of constructs to skip before starting to collect the result set.
            sort_by: Optional field to sort by.
            sort_dir: Optional sort direction ('asc' or 'desc').
            search: Optional search string to filter constructs.

        Returns:
            List of PreviewSchema representing the survey constructs.
        """
        constructs = await self.repo.get_paged(
            limit, offset, sort_by, sort_dir, search, SurveyConstructRepository.SEARCHABLE_COLUMNS
        )
        construct_previews = [PreviewSchema.model_validate(construct) for construct in constructs]
        return construct_previews

    async def get_survey_construct(self, construct_id: uuid.UUID) -> Optional[SurveyConstruct]:
        """Retrieve a specific survey construct by ID.

        Args:
            construct_id: Identifier of the survey construct.

        Returns:
            The SurveyConstruct object if found, else None.
        """
        return await self.repo.get(construct_id)

    async def get_construct_summary(self, construct_id: uuid.UUID) -> Optional[SurveyConstructSchema]:
        """Retrieve a summary of a survey construct.

        Args:
            construct_id: Identifier of the survey construct.

        Returns:
            SurveyConstructSchema representing the survey construct summary if found, else None.
        """
        # TODO: proposed feature => construct summary with usage statistics and response statistics
        construct_summary = await self.repo.get(construct_id)
        if not construct_summary:
            return None
        return SurveyConstructSchema.model_validate(construct_summary)

    async def get_construct_details(self, construct_id: uuid.UUID) -> Optional[SurveyConstructSchema]:
        """Retrieve detailed information about a survey construct.

        Args:
            construct_id: Identifier of the survey construct.

        Returns:
            SurveyConstructSchema representing the detailed survey construct if found, else None.
        """
        survey_construct = await self.repo.get(construct_id, options=SurveyConstructRepository.LOAD_FULL_DETAILS)
        if not survey_construct:
            return None
        return SurveyConstructSchema.model_validate(survey_construct)

    async def delete_survey_construct(self, construct_id: uuid.UUID) -> None:
        """Delete a survey construct by ID.

        Args:
            construct_id: Identifier of the survey construct to delete.

        Returns:
            None
        """
        await self.repo.delete(construct_id)

    # async def reorder_items(self, construct_id: uuid.UUID, items_map: dict) -> None:
    #     """Reorder items within a survey construct.

    #     Args:
    #         construct_id: Identifier of the survey construct.
    #         items_map: Mapping of item IDs to their new order.

    #     Returns:
    #         None
    #     """
    #     await self.item_repo.reorder_ordered_instances(construct_id, items_map)

    async def count_constructs(self, search: Optional[str] = None) -> int:
        """Count total survey constructs with optional search filter.

        Args:
            search: Optional search string to filter constructs.

        Returns:
            Total count of survey constructs.
        """
        return await self.repo.count(search)
