import uuid
from typing import List

from data.models.survey_constructs import SurveyConstruct
from data.repositories.survey_construct import SurveyConstructRepository


class SurveyConstructService:
	def __init__(self, construct_repo: SurveyConstructRepository):
		self.construct_repo = construct_repo

	async def get_survey_constructs(self) -> List[SurveyConstruct]:
		return await self.construct_repo.get_all()

	async def get_construct_summary(self, construct_id: uuid.UUID) -> SurveyConstruct:
		return await self.construct_repo.get_construct_summary(construct_id)

	async def get_construct_details(self, construct_id: uuid.UUID) -> SurveyConstruct:
		return await self.construct_repo.get_detailed_construct_object(construct_id)

	async def delete_survey_construct(self, construct_id: uuid.UUID) -> None:
		await self.construct_repo.delete(construct_id)
