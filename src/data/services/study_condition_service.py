import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import StudyCondition
from data.repositories.study import StudyRepository
from data.repositories.study_condition import StudyConditionRepository
from data.schemas.study_condition_schemas import StudyConditionCreateSchema, StudyConditionSchema


class StudyConditionService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.study_repo = StudyRepository(db)
		self.condition_repo = StudyConditionRepository(db)

	async def create_study_condition(self, study_condition_in: StudyConditionCreateSchema) -> StudyConditionSchema:
		study_condition = StudyCondition(
			name=study_condition_in.name,
			description=study_condition_in.description,
			study_id=study_condition_in.study_id,
		)
		created_condition = await self.condition_repo.create(study_condition)
		await self.db.commit()
		await self.db.refresh(created_condition)
		return StudyConditionSchema.model_validate(created_condition)

	async def copy_from(self, from_study_id: uuid.UUID, to_study_id: uuid.UUID) -> List[StudyConditionSchema]:
		conditions_to_copy = await self.get_study_conditions(from_study_id)
		new_conditions = []
		for condition in conditions_to_copy:
			new_condition = StudyCondition(
				name=condition.c.name, description=condition.c.description, study_id=to_study_id
			)
			created_condition = await self.condition_repo.create(new_condition)
			new_conditions.append(StudyConditionSchema.model_validate(created_condition))

		await self.db.commit()
		return new_conditions

	async def get_study_conditions(self, study_id: uuid.UUID) -> List[StudyCondition]:
		study_conditions = await self.condition_repo.get_conditions_by_study_id(study_id)

		return list(study_conditions)

	async def get_study_condition(self, condition_id: uuid.UUID) -> StudyCondition:
		condition = await self.condition_repo.get(condition_id)

		return condition
