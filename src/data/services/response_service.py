from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant_responses import SurveyItemResponse
from data.repositories.participant_response import SurveyItemResponseRepository
from data.schemas.survey_response_schemas import SurveyReponseCreateSchema


class ParticipantResponseService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.survey_item_response_repo = SurveyItemResponseRepository(db)

	async def insert_survey_item_response(self, survey_response_data: SurveyReponseCreateSchema):
		svy_responses = []
		for svy_content in survey_response_data.responses:
			for item_response in svy_content.items:
				svy_item_response = SurveyItemResponse(
					survey_response_data.participant_id,
					svy_content.content_id,
					item_response.item_id,
					item_response.response_id,
				)
				svy_responses.append(svy_item_response)
		_ = await self.survey_item_response_repo.create_all(svy_responses)
		await self.survey_item_response_repo.db.commit()
