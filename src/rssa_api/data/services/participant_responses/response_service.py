"""Service layer for managing participant responses in studies."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from functools import singledispatchmethod
from typing import Any, Union

from rssa_api.data.models.participant_responses import (
    ParticipantFreeformResponse,
    ParticipantRating,
    ParticipantStudyInteractionResponse,
    ParticipantSurveyResponse,
)
from rssa_api.data.repositories.participant_responses import (
    ParticipantFreeformResponseRepository,
    ParticipantRatingRepository,
    ParticipantStudyInteractionResponseRepository,
    ParticipantSurveyResponseRepository,
)
from rssa_api.data.schemas.participant_response_schemas import (
    ParticipantContentRatingPayload,
    RatedItemSchema,
    StudyInteractionResponseBaseSchema,
    StudyInteractionResponseSchema,
    SurveyItemResponseBaseSchema,
    SurveyItemResponseSchema,
    TextResponseBaseSchema,
    TextResponseSchema,
)
from rssa_api.data.utility import convert_datetime_to_str, convert_uuids_to_str

ResponseCreateUnionType = Union[
    SurveyItemResponseBaseSchema,
    StudyInteractionResponseBaseSchema,
    ParticipantContentRatingPayload,
    TextResponseBaseSchema,
]
ResponseUnionType = Union[SurveyItemResponseSchema, StudyInteractionResponseSchema, RatedItemSchema, TextResponseSchema]


class ResponseType(str, Enum):
    """Enumeration of participant response types."""

    SURVEY_ITEM = 'survey_item'
    STUDY_INTERACTION = 'study_interaction'
    TEXT_RESPONSE = 'text_response'
    CONTENT_RATING = 'content_rating'


class ParticipantResponseService:
    """Service for managing participant responses in studies.

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
        self.repo_map = {
            ResponseType.SURVEY_ITEM: item_response_repo,
            ResponseType.TEXT_RESPONSE: text_response_repo,
            ResponseType.CONTENT_RATING: content_rating_repo,
            ResponseType.STUDY_INTERACTION: interact_response_repo,
        }

        self.schema_map = {
            ResponseType.SURVEY_ITEM: SurveyItemResponseSchema,
            ResponseType.TEXT_RESPONSE: TextResponseSchema,
            ResponseType.CONTENT_RATING: RatedItemSchema,
            ResponseType.STUDY_INTERACTION: StudyInteractionResponseSchema,
        }
        self.item_repo = item_response_repo
        self.text_repo = text_response_repo

        self.rating_repo = content_rating_repo
        self.interact_response_repo = interact_response_repo

    async def get_response_for_page(
        self, response_type: ResponseType, study_id: uuid.UUID, participant_id: uuid.UUID, page_id: uuid.UUID
    ) -> list[ResponseUnionType]:
        """Retrieve a participant response by its type and associated identifiers.

        Args:
            response_type: The type of the response to retrieve.
            study_id: The ID of the study.
            participant_id: The ID of the participant.
            page_id: The ID of the page associated with the response.

        Returns:
            The corresponding response schema object, or None if not found.
        """
        repo = self.repo_map.get(response_type)
        if not repo:
            raise ValueError(f'Unsupported response type: {response_type}')
        response_items = await repo.get_all_by_fields(
            [('study_step_page_id', page_id), ('study_participant_id', participant_id), ('study_id', study_id)]
        )
        if not response_items:
            return []

        schema_cls = self.schema_map.get(response_type)
        if not schema_cls:
            raise ValueError(f'No schema found for response type: {response_type}')
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
        repo = self.repo_map.get(response_type)
        if not repo:
            raise ValueError(f'Unsupported response type: {response_type}')

        return await repo.update_response(response_id, update_dict, client_version)

    @singledispatchmethod
    async def create_response(  # noqa: D102
        self, study_id: uuid.UUID, participant_id: uuid.UUID, response_data: ResponseCreateUnionType
    ) -> ResponseUnionType:
        raise ValueError(f'Unsupported response data type: {type(response_data)}')

    @create_response.register
    async def _(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, rating_payload: ParticipantContentRatingPayload
    ) -> RatedItemSchema:
        """Creates a content rating for a participant."""
        content_rating = ParticipantRating(
            study_id=study_id,
            participant_id=participant_id,
            step_id=rating_payload.step_id,
            step_page_id=rating_payload.step_page_id,
            context_tag=rating_payload.context_tag,
            item_id=rating_payload.rated_item.item_id,
            item_table_name='movies',  # We will make this Dynamic when we add support for different content types
            rating=rating_payload.rated_item.rating,
            scale_min=1,  # This will be dependent on study design but current we only support 1 to 5
            scale_max=5,
        )

        await self.rating_repo.create(content_rating)
        return RatedItemSchema.model_validate(content_rating)

    @create_response.register
    async def _(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, response_data: StudyInteractionResponseBaseSchema
    ) -> StudyInteractionResponseSchema:
        raw_dict = response_data.payload_json.model_dump()
        json_safe_dict = convert_uuids_to_str(raw_dict)
        json_safe_dict = convert_datetime_to_str(json_safe_dict)
        int_response = ParticipantStudyInteractionResponse(
            study_id=study_id,
            participant_id=participant_id,
            step_id=response_data.step_id,
            step_page_id=response_data.step_page_id,
            context_tag=response_data.context_tag,
            payload_json=json_safe_dict,
        )
        await self.interact_response_repo.create(int_response)
        return StudyInteractionResponseSchema.model_validate(int_response)

    @create_response.register
    async def _(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, text_response_data: TextResponseBaseSchema
    ) -> TextResponseSchema:
        """Creates a single freeform text response."""
        new_response = ParticipantFreeformResponse(
            study_id=study_id,
            participant_id=participant_id,
            step_id=text_response_data.step_id,
            item_id=None,
            context_tag=text_response_data.context_tag,
            response_text=text_response_data.response_text,
            updated_at=datetime.now(timezone.utc),
            version=1,
        )
        await self.text_repo.create(new_response)
        return TextResponseSchema.model_validate(new_response)

    @create_response.register
    async def _(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, item_response: SurveyItemResponseBaseSchema
    ) -> SurveyItemResponseSchema:
        """Creates a single survey item response."""
        response_item = ParticipantSurveyResponse(
            study_id=study_id,
            step_id=item_response.step_id,
            step_page_id=item_response.step_page_id,
            participant_id=participant_id,
            construct_id=item_response.construct_id,
            item_id=item_response.item_id,
            scale_id=item_response.scale_id,
            scale_level_id=item_response.scale_level_id,
            context_tag=item_response.context_tag,
        )
        await self.item_repo.create(response_item)

        return SurveyItemResponseSchema.model_validate(response_item)
