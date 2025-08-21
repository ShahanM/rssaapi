import uuid
from typing import Optional, Union

from data.models.study_components import Step, Study, StudyCondition
from data.repositories.study import StudyRepository
from data.repositories.study_condition import StudyConditionRepository
from data.repositories.study_step import StudyStepRepository
from data.schemas.study_schemas import (
	ConditionCountSchema,
	StudyCreateSchema,
	StudySchema,
	StudySummarySchema,
)
from data.schemas.study_step_schemas import StudyStepSchema
from data.utility import sa_obj_to_dict


class StudyService:
	def __init__(
		self,
		study_repo: StudyRepository,
		step_repo: StudyStepRepository,
		condition_repo: StudyConditionRepository,
	):
		self.study_repo = study_repo
		self.study_step_repo = step_repo
		self.condition_repo = condition_repo

	async def create_new_study(self, study_in: StudyCreateSchema, created_by: str) -> StudySchema:
		study = Study(name=study_in.name, description=study_in.description, created_by=created_by)

		return await self.study_repo.create(study)

	async def get_all_studies(self) -> list[Study]:
		# FIXME: use start index and limit to page responses
		return await self.study_repo.get_all()

	async def get_study_by_id(self, study_id: uuid.UUID) -> Study:
		return await self.study_repo.get(study_id)

	async def get_studies_by_ownership(self, owner: str) -> list[Study]:
		return await self.study_repo.get_all_by_field('owner', owner)

	async def get_study_details(self, study_id: uuid.UUID) -> Study:
		study_obj = await self.study_repo.get_detailed_study_object(study_id)

		return study_obj

	async def get_study_summary(self, study_id: uuid.UUID) -> Optional[StudySummarySchema]:
		study_row = await self.study_repo.get_total_participants(study_id)
		if not study_row:
			return None
		print(study_row)
		study_obj = study_row[0]
		total_participants_count = study_row.total_participants

		study_data = sa_obj_to_dict(study_obj)
		study_data['total_participants'] = total_participants_count

		participants_by_condition_list = []
		condition_counts_rows = await self.condition_repo.get_participant_count_by_condition(study_id)
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
		self, study_id: uuid.UUID, created_by: str, new_study_name: Optional[str] = None
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

	async def get_first_step(self, study_id: uuid.UUID) -> Step:
		study_steps = await self.study_step_repo.get_steps_by_study_id(study_id)

		return study_steps[0]

	async def get_next_step(self, study_id: uuid.UUID, current_step_id: uuid.UUID) -> Optional[StudyStepSchema]:
		study_steps = await self.study_step_repo.get_steps_by_study_id(study_id)

		for i in range(len(study_steps)):
			if i >= len(study_steps) - 1:
				return None
			study_step = study_steps[i]
			if study_step.id == current_step_id:
				return StudyStepSchema.model_validate(study_steps[i + 1])
		else:
			return None

	async def get_study_steps(self, study_id: uuid.UUID) -> list[Step]:
		return await self.study_step_repo.get_steps_by_study_id(study_id)

	async def get_study_conditions(self, study_id: uuid.UUID) -> list[StudyCondition]:
		return await self.condition_repo.get_all_by_field('study_id', study_id)

	async def reorder_study_steps(self, study_id: uuid.UUID, steps_map: dict[uuid.UUID, int]) -> list[Step]:
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
