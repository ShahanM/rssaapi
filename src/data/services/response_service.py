import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant_responses import SurveyFreeformResponse, SurveyItemResponse
from data.repositories.participant_response import SurveyFreeformResponseRepository, SurveyItemResponseRepository
from data.schemas.survey_response_schemas import FreeformTextResponseCreateSchema, SurveyReponseCreateSchema


class ParticipantResponseService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.survey_item_response_repo = SurveyItemResponseRepository(db)
		self.freeform_response_repo = SurveyFreeformResponseRepository(db)

	async def create_survey_item_response(self, study_id: uuid.UUID, survey_response_data: SurveyReponseCreateSchema):
		svy_responses = []
		for svy_content in survey_response_data.responses:
			for item_response in svy_content.items:
				svy_item_response = SurveyItemResponse(
					study_id=study_id,
					participant_id=survey_response_data.participant_id,
					construct_id=svy_content.content_id,
					item_id=item_response.item_id,
					response=item_response.response_id,  # this is the id of the scale_level item
				)
				svy_responses.append(svy_item_response)
		_ = await self.survey_item_response_repo.create_all(svy_responses)
		await self.db.commit()

	async def create_freeform_text_response(
		self, study_id: uuid.UUID, text_response_data: FreeformTextResponseCreateSchema
	):
		text_responses = []
		for text_response in text_response_data.responses:
			txt_response_obj = SurveyFreeformResponse(
				study_id=study_id,
				participant_id=text_response_data.participant_id,
				step_id=text_response_data.step_id,
				item_id=None,
				context_tag=text_response.context_tag,
				response_text=text_response.response,
			)
			text_responses.append(txt_response_obj)
		_ = await self.freeform_response_repo.create_all(text_responses)
		await self.db.commit()
