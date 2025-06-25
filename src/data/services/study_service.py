import uuid
from typing import List, Union

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import Step, Study, StudyCondition
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
		"""_summary_

		Args:
			study_in (StudyCreateSchema): _description_
			created_by (str): _description_

		Returns:
			StudySchema: _description_
		"""
		study = Study(name=study_in.name, description=study_in.description, created_by=created_by)

		return await self.study_repo.create(study)

	async def get_all_studies(self) -> List[Study]:
		"""_summary_

		Returns:
			List[Study]: _description_
		"""
		# FIME: use start index and limit to page responses
		return await self.study_repo.get_all()

	async def get_study_by_id(self, study_id: uuid.UUID) -> Union[StudySchema, None]:
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_

		Returns:
			Union[StudySchema, None]: _description_
		"""
		return await self.study_repo.get(study_id)

	async def get_studies_by_ownership(self, owner: str) -> List[Study]:
		"""_summary_

		Args:
			owner (str): _description_

		Returns:
			Union[List[Study], None]: _description_
		"""
		return await self.study_repo.get_all_by_field('owner', owner)

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
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_
			created_by (str): _description_
			new_study_name (Union[str, None], optional): _description_. Defaults to None.

		Raises:
			ValueError: _description_

		Returns:
			Study: _description_
		"""
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
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_

		Returns:
			StudyStepSchema: _description_
		"""
		study_steps = await self.study_step_repo.get_steps_by_study_id(study_id)

		return StudyStepSchema.model_validate(study_steps[0])

	async def get_next_step(self, study_id: uuid.UUID, current_step_id: uuid.UUID) -> Union[StudyStepSchema, None]:
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_
			current_step_id (uuid.UUID): _description_

		Returns:
			Union[StudyStepSchema, None]: _description_
		"""
		study_steps = await self.study_step_repo.get_steps_by_study_id(study_id)

		for i in range(len(study_steps)):
			if i >= len(study_steps) - 1:
				return None
			study_step = study_steps[i]
			if study_step.id == current_step_id:
				return StudyStepSchema.model_validate(study_steps[i + 1])
		else:
			return None

	async def get_study_steps(self, study_id: uuid.UUID) -> List[Step]:
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_

		Returns:
			List[Step]: _description_
		"""
		return await self.study_step_repo.get_steps_by_study_id(study_id)

	async def get_study_conditions(self, study_id: uuid.UUID) -> List[StudyCondition]:
		return await self.condition_repo.get_all_by_field('study_id', study_id)
