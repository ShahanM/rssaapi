import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from data.models.participant_responses import FreeformResponse, StudyInteractionResponse, SurveyItemResponse
from data.repositories.participant_responses.participant_response import (
    FreeformResponseRepository,
    ParticipantRating,
    ParticipantRatingRepository,
    StudyInteractionResponseRepository,
    SurveyItemResponseRepository,
)
from data.schemas.participant_response_schemas import (
    ParticipantContentRatingPayload,
    RatedItemBaseSchema,
    RatedItemSchema,
    StudyInteractionResponseBaseSchema,
    StudyInteractionResponseSchema,
    SurveyItemResponseBaseSchema,
    SurveyItemResponseSchema,
    TextResponseCreateSchema,
    TextResponseSchema,
)
from data.utility import convert_datetime_to_str, convert_uuids_to_str


class ParticipantResponseService:
    def __init__(
        self,
        item_response_repo: SurveyItemResponseRepository,
        text_response_repo: FreeformResponseRepository,
        content_rating_repo: ParticipantRatingRepository,
        interact_response_repo: StudyInteractionResponseRepository,
    ):
        self.item_repo = item_response_repo
        self.text_repo = text_response_repo

        self.rating_repo = content_rating_repo
        self.interact_response_repo = interact_response_repo

    # ==========================================================================
    # SurveyItemResponseRepository
    # table: survey_item_responses
    # model: SurveyItemResponse
    # ==========================================================================
    async def create_item_response(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, item_response: SurveyItemResponseBaseSchema
    ) -> SurveyItemResponseSchema:
        response_item = SurveyItemResponse(
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

    async def update_item_response(
        self, response_id: uuid.UUID, update_dict: dict[str, Any], client_version: int
    ) -> bool:
        return await self.item_repo.update_response(response_id, update_dict, client_version)

    async def get_survey_page_response(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, page_id: uuid.UUID
    ) -> list[SurveyItemResponseSchema]:
        response_items = await self.item_repo.get_all_by_fields(
            [('step_page_id', page_id), ('participant_id', participant_id), ('study_id', study_id)]
        )
        if not response_items:
            return []
        return [SurveyItemResponseSchema.model_validate(resitm) for resitm in response_items]

    # ==============================================================================
    # StudyInteractionResponseRepository
    # table: study_interaction_responses
    # model: StudyInteractionResponse
    # ==============================================================================
    async def get_participant_interaction_responses(
        self, step_id: uuid.UUID, study_id: uuid.UUID, participant_id: uuid.UUID
    ) -> list[StudyInteractionResponseSchema]:
        responses = await self.interact_response_repo.get_all_by_fields(
            [('step_id', step_id), ('participant_id', participant_id), ('study_id', study_id)]
        )
        if not responses:
            return []
        return [StudyInteractionResponseSchema.model_validate(res_itm) for res_itm in responses]

    async def create_participant_interaction_response(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, response_data: StudyInteractionResponseBaseSchema
    ) -> StudyInteractionResponseSchema:
        raw_dict = response_data.payload_json.model_dump()
        json_safe_dict = convert_uuids_to_str(raw_dict)
        json_safe_dict = convert_datetime_to_str(json_safe_dict)
        int_response = StudyInteractionResponse(
            study_id=study_id,
            participant_id=participant_id,
            step_id=response_data.step_id,
            step_page_id=response_data.step_page_id,
            context_tag=response_data.context_tag,
            payload_json=json_safe_dict,
        )
        await self.interact_response_repo.create(int_response)
        return StudyInteractionResponseSchema.model_validate(int_response)

    async def update_participant_interaction_response(
        self, response_id: uuid.UUID, update_dict: dict[str, Any], client_version: int
    ) -> bool:
        return await self.interact_response_repo.update_response(response_id, update_dict, client_version)

    # ==============================================================================
    # FreeformResponseRepository
    # table: freeform_responses
    # model: FreeformResponse
    # ==============================================================================
    async def create_or_update_text_responses(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, text_response_data: TextResponseCreateSchema
    ) -> None:
        response_items = await self.text_repo.get_all_by_fields(
            [
                ('study_id', study_id),
                ('step_id', text_response_data.step_id),
                ('participant_id', participant_id),
            ]
        )
        db_responses = {dbres.context_tag: dbres for dbres in response_items}
        responses_to_update = []
        responses_to_create = []

        for tres in text_response_data.responses:
            db_res = db_responses.get(tres.context_tag)
            if db_res:
                responses_to_update.append(
                    (db_res.id, {'response_text': tres.response_text, 'version': db_res.version + 1})
                )
            else:
                responses_to_create.append(
                    FreeformResponse(
                        study_id=study_id,
                        participant_id=participant_id,
                        step_id=text_response_data.step_id,
                        item_id=None,
                        context_tag=tres.context_tag,
                        response_text=tres.response_text,
                        updated_at=datetime.now(timezone.utc),
                        version=1,
                    )
                )

        for res_id, update_data in responses_to_update:
            await self.text_repo.update(res_id, update_data)

        await self.text_repo.create_all(responses_to_create)

    async def get_participant_text_responses(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, step_id: uuid.UUID
    ) -> list[TextResponseSchema]:
        response_items = await self.text_repo.get_all_by_fields(
            [
                ('study_id', study_id),
                ('step_id', step_id),
                ('participant_id', participant_id),
            ]
        )
        if not response_items:
            return []
        return [TextResponseSchema.model_validate(item) for item in response_items]

    # ==============================================================================
    # ParticipantRatingRepository
    # table: study_interaction_responses
    # model: StudyInteractionResponse
    # ==============================================================================
    async def create_content_rating(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, rating_payload: ParticipantContentRatingPayload
    ) -> RatedItemSchema:
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

    async def update_content_rating(
        self, rating_id: uuid.UUID, update_dict: dict[str, Any], client_version: int
    ) -> bool:
        return await self.rating_repo.update_response(rating_id, update_dict, client_version)

    async def get_ratings_for_participants(
        self, study_id: uuid.UUID, participant_id: uuid.UUID
    ) -> list[RatedItemSchema]:
        ratings = await self.rating_repo.get_all_by_fields([('participant_id', participant_id), ('study_id', study_id)])
        if not ratings:
            return []

        return [RatedItemSchema.model_validate(rating) for rating in ratings]
