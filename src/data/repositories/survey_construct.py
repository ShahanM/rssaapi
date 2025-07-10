import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models.survey_constructs import ConstructScale, SurveyConstruct
from data.repositories.base_repo import BaseRepository


class SurveyConstructRepository(BaseRepository[SurveyConstruct]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, SurveyConstruct)

	async def get_construct_summary(self, construct_id: uuid.UUID) -> SurveyConstruct:
		query = (
			select(SurveyConstruct)
			.where(SurveyConstruct.id == construct_id)
			.options(selectinload(SurveyConstruct.construct_type), selectinload(SurveyConstruct.construct_scale))
		)

		result = await self.db.execute(query)
		return result.scalar_one_or_none()

	async def get_detailed_construct_object(self, construct_id: uuid.UUID) -> SurveyConstruct:
		query = (
			select(SurveyConstruct)
			.where(SurveyConstruct.id == construct_id)
			.options(
				selectinload(SurveyConstruct.construct_type),
				selectinload(SurveyConstruct.construct_scale).selectinload(ConstructScale.scale_levels),
				selectinload(SurveyConstruct.items),
			)
		)

		result = await self.db.execute(query)
		return result.scalar_one_or_none()
