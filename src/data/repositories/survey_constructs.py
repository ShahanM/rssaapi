import uuid
from operator import attrgetter
from typing import Dict, Union

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models.survey_constructs import (
	ConstructItem,
	ConstructScale,
	ScaleLevel,
	SurveyConstruct,
)
from data.repositories.base_ordered_repo import BaseOrderedRepository
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
				selectinload(SurveyConstruct.items),
			)
		)

		result = await self.db.execute(query)
		return result.scalar_one_or_none()


class ConstructScaleRepository(BaseRepository[ConstructScale]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, ConstructScale)

	async def get_details(self, scale_id: uuid.UUID) -> ConstructScale:
		query = (
			select(ConstructScale)
			.where(ConstructScale.id == scale_id)
			.options(selectinload(ConstructScale.scale_levels))
		)

		result = await self.db.execute(query)
		return result.scalar_one_or_none()


# class ConstructItemRepository(BaseRepository[ConstructItem]):
# 	def __init__(self, db: AsyncSession):
# 		super().__init__(db, ConstructItem)

# 	async def get_last_item(self, construct_id: uuid.UUID) -> Union[ConstructItem, None]:
# 		query = (
# 			select(ConstructItem)
# 			.where(ConstructItem.construct_id == construct_id)
# 			.order_by(ConstructItem.order_position.desc())
# 		)
# 		result = await self.db.execute(query)
# 		last_item = result.scalars().first()

# 		return last_item

# 	async def delete_ordered_item(self, item_id: uuid.UUID) -> None:
# 		query = select(ConstructItem).where(ConstructItem.id == item_id)
# 		result = await self.db.execute(query)
# 		item_to_delete = result.scalar_one_or_none()

# 		if not item_to_delete:
# 			print(f'Error: Item with ID {item_id} not found.')
# 			return

# 		deleted_position = item_to_delete.order_position
# 		parent_id = item_to_delete.construct_id

# 		await self.db.delete(item_to_delete)

# 		update_stmt = (
# 			update(ConstructItem)
# 			.where(ConstructItem.construct_id == parent_id, ConstructItem.order_position > deleted_position)
# 			.values(order_position=ConstructItem.order_position - 1)
# 		)

# 		await self.db.execute(update_stmt)

# 		await self.db.commit()


class ConstructItemRepository(BaseOrderedRepository[ConstructItem]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, ConstructItem, parent_id_column_name='construct_id')


class ScaleLevelRepository(BaseOrderedRepository[ScaleLevel]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, ScaleLevel, parent_id_column_name='scale_id')

	# async def get_last_scale_level(self, scale_id: uuid.UUID) -> Union[ScaleLevel, None]:
	# 	query = select(ScaleLevel).where(ScaleLevel.scale_id == scale_id).order_by(ScaleLevel.order_position.desc())
	# 	result = await self.db.execute(query)
	# 	last_level = result.scalars().first()

	# 	return last_level

	# async def reorder_scale_levels(self, scale_id: uuid.UUID, levels_map: Dict[uuid.UUID, int]):
	# 	query = select(ScaleLevel).where(ScaleLevel.scale_id == scale_id)
	# 	scale_level_orm = await self.db.execute(query)
	# 	scale_levels_in_db = scale_level_orm.scalars().all()

	# 	levels_with_target_pos = []
	# 	level_orm_by_id = {level.id: level for level in scale_levels_in_db}

	# 	for level_id, level_orm in level_orm_by_id.items():
	# 		target_pos = levels_map.get(level_id, level_orm.order_position)
	# 		levels_with_target_pos.append({'id': level_id, 'current_orm': level_orm, 'target_pos': target_pos})
	# 	levels_with_target_pos.sort(key=lambda x: (x['target_pos'], x['current_orm'].order_position))

	# 	current_sequnetial_pos = 1
	# 	for level_data in levels_with_target_pos:
	# 		level_data['current_orm'].order_position = current_sequnetial_pos
	# 		current_sequnetial_pos += 1

	# await self.db.flush()

	# return sorted(scale_levels_in_db, key=attrgetter('order_position'))
