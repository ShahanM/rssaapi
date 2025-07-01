import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import Page, Step
from data.repositories.page import PageRepository
from data.repositories.study_step import StudyStepRepository
from data.schemas.study_step_schemas import StudyStepCreateSchema, StudyStepDetailSchema


class StudyStepService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.study_step_repo = StudyStepRepository(db)
		self.step_page_repo = PageRepository(db)

	async def create_study_step(self, new_step: StudyStepCreateSchema) -> Step:
		study_step = Step(
			name=new_step.name,
			order_position=new_step.order_position,
			description=new_step.description,
			study_id=new_step.study_id,
		)
		await self.study_step_repo.create(study_step)

		await self.db.commit()
		await self.db.refresh(study_step)

		return study_step

	async def get_study_step(self, study_step_id: uuid.UUID) -> Optional[Step]:
		return await self.study_step_repo.get(study_step_id)

	async def get_study_step_with_pages(self, study_step_id: uuid.UUID) -> Step:
		return await self.study_step_repo.get_study_step_with_pages(study_step_id)

	async def get_pages_for_step(self, study_step_id: uuid.UUID) -> List[Page]:
		return await self.step_page_repo.get_all_by_field('step_id', study_step_id)
