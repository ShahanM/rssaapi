import uuid
from typing import List, Union

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from data.models.study_components import Step

from .base_repo import BaseRepository


class StudyStepSchema(BaseModel):
	id: Union[uuid.UUID, None] = None
	name: str
	description: str
	order_position: int
	study_id: uuid.UUID

	class Config:
		orm_mode = True
		model_config = ConfigDict(from_attributes=True)


class StudyStepRepository(BaseRepository):
	def __init__(self, db: AsyncSession):
		super().__init__(db, Step)

	async def create_study_steps(self, study_id: uuid.UUID, steps: List[StudyStepSchema]) -> List[Step]:
		study_steps = []
		for step in steps:
			study_step = Step(
				name=step.name,
				order_position=step.order_position,
				description=step.description,
				study_id=study_id,
			)
			self.db.add(study_step)
			study_steps.append(study_step)
		await self.db.commit()
		for step in study_steps:
			await self.db.refresh(step)

		return study_steps

	async def get_steps_by_study_id(self, study_id: uuid.UUID) -> List[Step]:
		query = (
			select(Step)
			.where(Step.study_id == study_id)
			.order_by(asc(Step.order_position))
			.options(selectinload(Step.pages))
		)
		result = await self.db.execute(query)
		steps = result.scalars().all()

		return list(steps)

	# async def copy_steps_from(self, from_study_id: uuid.UUID, to_study_id: uuid.UUID) -> List[Step]:
	# 	steps_to_copy = await self.get_steps_by_study_id(from_study_id)
	# 	new_steps = []
	# 	page_repo = PageRepository(self.db)  # Instantiate PageRepository

	# 	for step in steps_to_copy:
	# 		new_step = Step(
	# 			name=step.c.name,
	# 			order_position=step.c.order_position,
	# 			description=step.c.description,
	# 			study_id=to_study_id,
	# 		)
	# 		self.db.add(new_step)
	# 		new_steps.append(new_step)

	# 	await self.db.commit()
	# 	for new_step in new_steps:
	# 		await self.db.refresh(new_step)
	# 		# Delegate page copying to PageRepository
	# 		await page_repo.copy_pages_from(from_step_id=step.c.id, to_step_id=new_step.id, new_study_id=to_study_id)

	# 	return new_steps

	async def get_study_step_by_id(self, step_id: uuid.UUID) -> Step:
		query = select(Step).where(Step.id == step_id)
		result = await self.db.execute(query)
		step = result.scalars().first()
		if not step:
			raise HTTPException(status_code=404, detail='Study step not found')

		return step

	async def get_first_step(self, study_id: uuid.UUID) -> Step:
		query = select(Step).where(Step.c.study_id == study_id).order_by(Step.c.order_position)
		result = await self.db.execute(query)
		step = result.scalars().first()

		return step

	async def get_next_step(self, study_id: uuid.UUID, current_step_id: uuid.UUID) -> Union[Step, None]:
		query = select(Step).where(Step.id == current_step_id)
		result = await self.db.execute(query)
		current = result.scalars().first()
		if not current:
			raise HTTPException(status_code=404, detail='Current step not found')

		query = select(Step).where(Step.c.study_id == study_id, Step.c.order_position > current.order_position)
		result = await self.db.execute(query)
		steps = result.scalars().all()
		if not steps:
			# No more steps
			return None

		# FIXME: if we are on the last one, then next step should always send to a default study has ended step
		step = steps[0]
		if not step:
			raise HTTPException(status_code=404, detail='Next step not found')

		return step
