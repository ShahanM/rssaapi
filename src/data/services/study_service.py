import uuid
from typing import Union

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study import Study, StudyCondition
from data.repositories.study import StudyRepository
from data.repositories.study_condition import StudyConditionRepository
from data.repositories.study_step import StudyStepRepository
from data.schemas.study_condition_schemas import StudyConditionSchema
from data.schemas.study_schemas import StudyCreateSchema, StudyDetailSchema, StudySchema
from data.schemas.study_step_schemas import StudyStepSchema


class StudyService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.study_repo = StudyRepository(db)
		self.study_step_repo = StudyStepRepository(db)
		self.condition_repo = StudyConditionRepository(db)

	async def create_new_study(self, study_in: StudyCreateSchema, created_by: str) -> StudySchema:
		"""
		Create a new study
		"""
		study = Study(name=study_in.name, description=study_in.description, created_by=created_by)

		return await self.study_repo.create(study)

	async def get_study_by_id(self, study_id: uuid.UUID) -> Union[StudySchema, None]:
		return await self.study_repo.get(study_id)

	async def get_study_details(self, study_id: uuid.UUID) -> Union[StudyDetailSchema, None]:
		"""
		Get study details by ID
		"""
		study = await self.study_repo.get(study_id)
		if not study:
			return None

		conditions = await self.condition_repo.get_conditions_by_study_id(study_id)

		validated_conditions = []
		if conditions:
			validated_conditions = [StudyConditionSchema.model_validate(condition) for condition in conditions]

		study_detail = StudyDetailSchema.model_validate(study)
		study_detail.conditions = validated_conditions

		return study_detail

	async def duplicate_study(
		self, study_id: uuid.UUID, created_by: str, new_study_name: Union[str, None] = None
	) -> Study:
		original_study = await self.study_repo.get(study_id)
		if not original_study:
			raise ValueError('Study not found')

		copy_name = new_study_name if new_study_name else f'{original_study.name} (copy)'
		new_study = Study(name=copy_name, description=original_study.c.description, created_by=created_by)
		new_study = await self.study_repo.create(new_study)

		conditions = await self.condition_repo.get_conditions_by_study_id(study_id)
		for condition in conditions:
			new_condition = StudyCondition(
				name=condition.c.name, description=condition.c.description, study_id=new_study.c.id
			)
			await self.condition_repo.create(new_condition)

		return new_study

	async def get_first_step(self, study_id: uuid.UUID) -> StudyStepSchema:
		study_steps = await self.study_step_repo.get_steps_by_study_id(study_id)

		return StudyStepSchema.model_validate(study_steps[0])

	async def get_next_step(self, study_id: uuid.UUID, current_step_id: uuid.UUID) -> Union[StudyStepSchema, None]:
		study_steps = await self.study_step_repo.get_steps_by_study_id(study_id)

		for i in range(len(study_steps)):
			if i >= len(study_steps) - 1:
				return None
			study_step = study_steps[i]
			if study_step.id == current_step_id:
				return StudyStepSchema.model_validate(study_steps[i + 1])
		else:
			return None
