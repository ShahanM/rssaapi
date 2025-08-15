import uuid
from typing import Dict, List, Union

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from data.models.study_components import Step, Study, StudyCondition
from data.models.study_participants import StudyParticipant
from data.repositories.study import StudyRepository
from data.repositories.study_condition import StudyConditionRepository
from data.repositories.study_step import StudyStepRepository
from data.schemas.study_condition_schemas import StudyConditionSchema
from data.schemas.study_schemas import (
	ConditionCountSchema,
	StudyCreateSchema,
	StudyDetailSchema,
	StudySchema,
	StudySummarySchema,
)
from data.schemas.study_step_schemas import StepsReorderItem, StudyStepSchema
from data.utility import sa_obj_to_dict


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

	async def get_study_by_id(self, study_id: uuid.UUID) -> Study:
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_

		Returns:
			Study: _description_
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

	async def get_study_details(self, study_id: uuid.UUID) -> Study:
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_

		Returns:
			Study: _description_
		"""

		study_obj = await self.study_repo.get_detailed_study_object(study_id)

		return study_obj

	async def get_study_summary(self, study_id: uuid.UUID) -> StudySummarySchema:
		study_query = (
			select(Study, func.count(StudyParticipant.id).label('total_participants'))
			.join_from(Study, StudyParticipant, Study.id == StudyParticipant.study_id, isouter=True)
			.where(Study.id == study_id)
			.group_by(Study.id, Study.name, Study.description, Study.date_created, Study.created_by, Study.owner)
		)

		condition_counts_query = (
			select(
				StudyCondition.id.label('condition_id'),
				StudyCondition.name.label('condition_name'),
				func.count(StudyParticipant.id).label('participant_count'),
			)
			.join(StudyParticipant, StudyParticipant.condition_id == StudyCondition.id, isouter=True)
			.where(StudyCondition.study_id == study_id)
			.group_by(StudyCondition.id, StudyCondition.name)
			.order_by(StudyCondition.name)
		)

		study_result = await self.db.execute(study_query)
		study_row = study_result.first()

		if not study_row:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

		study_obj = study_row[0]
		total_participants_count = study_row.total_participants

		condition_counts_result = await self.db.execute(condition_counts_query)
		condition_counts_rows = condition_counts_result.all()

		study_data = sa_obj_to_dict(study_obj)
		study_data['total_participants'] = total_participants_count

		participants_by_condition_list = []
		for row in condition_counts_rows:
			participants_by_condition_list.append(
				ConditionCountSchema(
					condition_id=row.condition_id,
					condition_name=row.condition_name,
					participant_count=row.participant_count,
				).model_dump()
			)
		study_data['participants_by_condition'] = participants_by_condition_list

		return StudySummarySchema.model_validate(study_data)

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

	async def reorder_study_steps(self, study_id: uuid.UUID, steps_map: Dict[uuid.UUID, int]) -> List[Step]:
		reordered_steps = await self.study_step_repo.reorder_study_steps(study_id, steps_map)

		return reordered_steps

	async def export_study_config(
		self, study_id: uuid.UUID
	) -> dict[str, Union[uuid.UUID, list[dict[str, uuid.UUID]], dict[str, uuid.UUID]]]:
		study_details = await self.get_study_details(study_id)

		study_config = {
			'study_id': study_details.id,
			'study_steps': [
				{step.name: step.id} for step in sorted(study_details.steps, key=lambda s: s.order_position)
			],
			'conditions': {cond.name: cond.id for cond in study_details.conditions},
		}

		return study_config
