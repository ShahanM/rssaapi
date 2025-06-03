from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import Step
from data.repositories.study_step import StudyStepRepository
from data.schemas.study_step_schemas import StudyStepCreateSchema, StudyStepSchema


class StudyStepService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.study_step_repo = StudyStepRepository(db)

	async def create_study_step(self, new_step: StudyStepCreateSchema) -> StudyStepSchema:
		study_step = Step(
			name=new_step.name,
			order_position=new_step.order_position,
			description=new_step.description,
			study_id=new_step.study_id,
		)
		await self.study_step_repo.create(study_step)

		await self.db.commit()
		await self.db.refresh(study_step)

		return StudyStepSchema.model_validate(study_step)
