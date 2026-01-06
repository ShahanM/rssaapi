"""Service layer for managing participant responses in studies."""

import uuid
from datetime import UTC, datetime
from enum import Enum
from functools import singledispatchmethod
from typing import Any

from rssa_storage.rssadb.models.participant_responses import (
    ParticipantFreeformResponse,
    ParticipantRating,
    ParticipantStudyInteractionResponse,
    ParticipantSurveyResponse,
)
from rssa_storage.rssadb.repositories.participant_responses import (
    ParticipantFreeformResponseRepository,
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
    ParticipantSurveyResponseRepository,
)
from rssa_storage.shared import RepoQueryOptions

from rssa_api.data.schemas.participant_response_schemas import (
    ParticipantFreeformResponseCreate,
    ParticipantFreeformResponseRead,
    ParticipantRatingBase,
    ParticipantRatingRead,
    ParticipantStudyInteractionResponseCreate,
    ParticipantStudyInteractionResponseRead,
    ParticipantSurveyResponseCreate,
    ParticipantSurveyResponseRead,
)
from rssa_api.data.utility import convert_datetime_to_str, convert_uuids_to_str

ResponseCreateUnionType = (
    ParticipantSurveyResponseCreate
    | ParticipantStudyInteractionResponseCreate
    | ParticipantRatingBase
    | ParticipantFreeformResponseCreate
)

ResponseSchemaType = (
    ParticipantSurveyResponseRead
    | ParticipantStudyInteractionResponseRead
    | ParticipantRatingRead
    | ParticipantFreeformResponseRead
)


class ResponseType(str, Enum):
    """Enumeration of participant response types."""

    SURVEY_ITEM = 'survey_item'
    STUDY_INTERACTION = 'study_interaction'
    TEXT_RESPONSE = 'text_response'
    CONTENT_RATING = 'content_rating'


class ParticipantResponseService:
    """Orchestration service for managing participant responses in studies.

    This service provides methods to create, update, and retrieve various types of participant responses,
    including survey item responses, freeform text responses, and content ratings.

    Attributes:
        item_repo: Repository for survey item responses.
        text_repo: Repository for freeform text responses.
        rating_repo: Repository for participant ratings.
        interact_response_repo: Repository for study interaction responses.
    """

    def __init__(
        self,
        item_response_repo: ParticipantSurveyResponseRepository,
        text_response_repo: ParticipantFreeformResponseRepository,
        content_rating_repo: ParticipantRatingRepository,
        interact_response_repo: ParticipantStudyInteractionResponseRepository,
    ):
        """Initialize the ParticipantResponseService with the necessary repositories.

        Args:
            item_response_repo: Repository for survey item responses.
            text_response_repo: Repository for freeform text responses.
            content_rating_repo: Repository for participant ratings.
            interact_response_repo: Repository for study interaction responses.
        """
        self.item_repo = item_response_repo
        self.text_repo = text_response_repo
        self.rating_repo = content_rating_repo
        self.interact_repo = interact_response_repo

        self.strategy_map = {
            ResponseType.SURVEY_ITEM: (item_response_repo, ParticipantSurveyResponseRead),
            ResponseType.TEXT_RESPONSE: (text_response_repo, ParticipantFreeformResponseRead),
            ResponseType.CONTENT_RATING: (content_rating_repo, ParticipantRatingRead),
            ResponseType.STUDY_INTERACTION: (interact_response_repo, ParticipantStudyInteractionResponseRead),
        }

    def _get_strategy(self, response_type: ResponseType):
        """Helper to get repo and schema for a response type."""
        if response_type not in self.strategy_map:
            raise ValueError(f'Unsupported response type: {response_type}')
        return self.strategy_map[response_type]

    async def get_response_for_page(
        self,
        response_type: ResponseType,
        study_id: uuid.UUID,
        participant_id: uuid.UUID,
        page_id: uuid.UUID | None = None,
    ) -> list[ResponseSchemaType]:
        """Retrieve a participant response by its type and associated identifiers.

        Args:
            response_type: The type of the response to retrieve.
            study_id: The ID of the study.
            participant_id: The ID of the participant.
            page_id: The ID of the page associated with the response.

        Returns:
            The corresponding response schema object, or None if not found.
        """
        repo, schema_cls = self._get_strategy(response_type)

        filters = {
            'study_participant_id': participant_id,
            'study_id': study_id,
        }
        if page_id is not None:
            filters['study_step_page_id'] = page_id

        repo_options = RepoQueryOptions(filters=filters)
        response_items = await repo.find_many(repo_options)
        return [schema_cls.model_validate(resitm) for resitm in response_items]

    async def get_response_for_step(
        self,
        response_type: ResponseType,
        study_id: uuid.UUID,
        participant_id: uuid.UUID,
        step_id: uuid.UUID | None = None,
    ) -> list[ResponseSchemaType]:
        """Retrieve a participant response by its type and step identifier.

        Args:
            response_type: The type of the response to retrieve.
            study_id: The ID of the study.
            participant_id: The ID of the participant.
            step_id: The ID of the step associated with the response.

        Returns:
            The corresponding response schema object, or None if not found.
        """
        repo, schema_cls = self._get_strategy(response_type)

        filters = {
            'study_participant_id': participant_id,
            'study_id': study_id,
        }
        if step_id is not None:
            filters['study_step_id'] = step_id

        repo_options = RepoQueryOptions(filters=filters)
        response_items = await repo.find_many(repo_options)
        return [schema_cls.model_validate(resitm) for resitm in response_items]

    async def update_response(
        self,
        response_type: ResponseType,
        response_id: uuid.UUID,
        update_dict: dict[str, Any],
        client_version: int,
    ) -> bool:
        """Updates a participant response based on its type.

        Args:
            response_type: The type of the response to update.
            response_id: The ID of the response to update.
            update_dict: A dictionary of fields to update.
            client_version: The version of the resource from the client for concurrency control.

        Returns:
            A boolean indicating whether the update was successful.
        """
        repo, _ = self._get_strategy(response_type)
        return await repo.update_response(response_id, update_dict, client_version)

    @singledispatchmethod
    async def create_response(  # noqa: D102
        self, response_data: ResponseCreateUnionType, study_id: uuid.UUID, participant_id: uuid.UUID
    ) -> ResponseSchemaType:
        raise ValueError(f'Unsupported response data type: {type(response_data)}')

    @create_response.register
    async def _(
        self, rating_payload: ParticipantRatingBase, study_id: uuid.UUID, participant_id: uuid.UUID
    ) -> ParticipantRatingRead:
        """Creates a content rating for a participant."""
        content_rating = ParticipantRating(
            study_id=study_id,
            study_participant_id=participant_id,
            study_step_id=rating_payload.study_step_id,
            study_step_page_id=rating_payload.study_step_page_id,
            context_tag=rating_payload.context_tag,
            item_id=rating_payload.rated_item.item_id,
            item_table_name='movies',  # We will make this Dynamic when we add support for different content types
            rating=rating_payload.rated_item.rating,
            scale_min=1,  # This will be dependent on study design but current we only support 1 to 5
            scale_max=5,
        )

        new_rating = await self.rating_repo.create(content_rating)
        return ParticipantRatingRead.model_validate(new_rating)

    @create_response.register
    async def _(
        self, response_data: ParticipantStudyInteractionResponseCreate, study_id: uuid.UUID, participant_id: uuid.UUID
    ) -> ParticipantStudyInteractionResponseRead:
        raw_dict = response_data.payload_json.model_dump()
        json_safe_dict = convert_uuids_to_str(raw_dict)
        json_safe_dict = convert_datetime_to_str(json_safe_dict)
        int_response = ParticipantStudyInteractionResponse(
            study_id=study_id,
            study_participant_id=participant_id,
            study_step_id=response_data.study_step_id,
            study_step_page_id=response_data.study_step_page_id,
            context_tag=response_data.context_tag,
            payload_json=json_safe_dict,
        )
        await self.interact_repo.create(int_response)
        return ParticipantStudyInteractionResponseRead.model_validate(int_response)

    @create_response.register
    async def _(
        self, text_response_data: ParticipantFreeformResponseCreate, study_id: uuid.UUID, participant_id: uuid.UUID
    ) -> ParticipantFreeformResponseRead:
        """Creates or updates a single freeform text response."""
        # Check for existing response relative to generic context tag constraint
        # Constraint: (study_id, study_participant_id, context_tag)
        existing = await self.text_repo.find_one(
            RepoQueryOptions(
                filters={
                    'study_id': study_id,
                    'study_participant_id': participant_id,
                    'context_tag': text_response_data.context_tag,
                }
            )
        )

        if existing:
            # Update
            updated_fields = {
                'response_text': text_response_data.response_text,
                'updated_at': datetime.now(UTC),
            }
            # Handle study_step_id update if provided? Model has it.
            if text_response_data.study_step_id:
                updated_fields['study_step_id'] = text_response_data.study_step_id

            result = await self.text_repo.update(existing.id, updated_fields)
            return ParticipantFreeformResponseRead.model_validate(result)

        new_response = ParticipantFreeformResponse(
            study_id=study_id,
            study_participant_id=participant_id,
            study_step_id=text_response_data.study_step_id,
            context_tag=text_response_data.context_tag,
            response_text=text_response_data.response_text,
            updated_at=datetime.now(UTC),
            version=1,
        )
        await self.text_repo.create(new_response)
        return ParticipantFreeformResponseRead.model_validate(new_response)

    @create_response.register
    async def _(
        self, item_response: ParticipantSurveyResponseCreate, study_id: uuid.UUID, participant_id: uuid.UUID
    ) -> ParticipantSurveyResponseRead:
        """Creates a single survey item response."""
        response_item = ParticipantSurveyResponse(
            study_id=study_id,
            study_step_id=item_response.study_step_id,
            study_step_page_id=item_response.study_step_page_id,
            study_participant_id=participant_id,
            survey_construct_id=item_response.survey_construct_id,
            survey_item_id=item_response.survey_item_id,
            survey_scale_id=item_response.survey_scale_id,
            survey_scale_level_id=item_response.survey_scale_level_id,
            context_tag=item_response.context_tag,
        )
        await self.item_repo.create(response_item)
        return ParticipantSurveyResponseRead.model_validate(response_item)
