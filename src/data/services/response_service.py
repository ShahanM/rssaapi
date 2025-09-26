import uuid
from datetime import datetime, timezone

from data.models.participant_behavior import ContentRating
from data.models.participant_responses import FreeformResponse, SurveyItemResponse
from data.repositories.participant_response import (
    ContentRatingRepository,
    FreeformResponseRepository,
    InteractionLoggingRepository,
    SurveyItemResponseRepository,
)
from data.schemas.participant_response_schemas import (
    RatedItemBaseSchema,
    RatedItemSchema,
    SurveyItemResponseBaseSchema,
    TextResponseCreateSchema,
    TextResponseSchema,
)


class ParticipantResponseService:
    def __init__(
        self,
        item_response_repo: SurveyItemResponseRepository,
        text_response_repo: FreeformResponseRepository,
        content_rating_repo: ContentRatingRepository,
        interaction_logging_repo: InteractionLoggingRepository,
    ):
        self.item_repo = item_response_repo
        self.text_repo = text_response_repo

        self.rating_repo = content_rating_repo
        self.logging_repo = interaction_logging_repo

    async def create_or_update_item_response(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, item_response: SurveyItemResponseBaseSchema
    ) -> int:
        response_item = await self.item_repo.get_by_fields(
            [
                ('study_id', study_id),
                ('participant_id', participant_id),
                ('construct_id', item_response.construct_id),
                ('item_id', item_response.item_id),
                ('scale_id', item_response.scale_id),
            ]
        )
        if response_item:
            await self.item_repo.update(
                response_item.id, {'scale_level_id': item_response.scale_level_id, 'version': response_item.version + 1}
            )
        else:
            response_item = SurveyItemResponse(
                study_id=study_id,
                participant_id=participant_id,
                construct_id=item_response.construct_id,
                item_id=item_response.item_id,
                scale_id=item_response.scale_id,
                scale_level_id=item_response.scale_level_id,
                updated_at=datetime.now(timezone.utc),
                version=1,
            )
            await self.item_repo.create(response_item)

        return response_item.version

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

    async def create_or_update_content_rating(self, participant_id: uuid.UUID, rated_item: RatedItemBaseSchema) -> None:
        content_rating = await self.rating_repo.get_by_fields(
            [
                ('participant_id', participant_id),
                ('item_id', rated_item.item_id),
            ]
        )
        if content_rating:
            await self.rating_repo.update(
                content_rating.id, {'rating': rated_item.rating, 'version': content_rating.version}
            )
        else:
            new_content_rating = ContentRating(
                participant_id=participant_id,
                item_id=rated_item.item_id,
                item_table_name='movies',  # We will make this Dynamic when we add support for different content types
                rating=rated_item.rating,
                scale_min=1,  # This will be dependent on study design but current we only support 1 to 5
                scale_max=5,
                version=1,
            )

            await self.rating_repo.create(new_content_rating)

    async def get_ratings_for_participants(self, participant_id) -> list[RatedItemSchema]:
        ratings = await self.rating_repo.get_all_by_field('participant_id', participant_id)
        if not ratings:
            return []

        return [RatedItemSchema.model_validate(rating) for rating in ratings]
