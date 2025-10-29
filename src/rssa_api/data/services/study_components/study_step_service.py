import uuid
from typing import Optional

from rssa_api.data.models.study_components import StudyStep
from rssa_api.data.repositories.study_components.study_step import StudyStepRepository
from rssa_api.data.schemas.base_schemas import OrderedListItem
from rssa_api.data.schemas.study_components import StudyStepBaseSchema, StudyStepNavigationSchema, StudyStepSchema


class StudyStepService:
    def __init__(self, step_repo: StudyStepRepository):
        self.repo = step_repo

    async def create_study_step(self, study_id: uuid.UUID, new_step: StudyStepBaseSchema) -> None:
        last_step = await self.repo.get_last_ordered_instance(study_id)
        next_order_pos = 1 if last_step is None else last_step.order_position + 1
        study_step = StudyStep(
            name=new_step.name,
            step_type=new_step.step_type,
            order_position=next_order_pos,
            description=new_step.description,
            study_id=study_id,
            path=new_step.path,
        )
        await self.repo.create(study_step)

    async def update_study_step(self, study_step_id: uuid.UUID, update_data: dict[str, str]) -> None:
        await self.repo.update(study_step_id, update_data)

    async def get_study_step(self, study_step_id: uuid.UUID) -> Optional[StudyStepSchema]:
        step = await self.repo.get(study_step_id)
        if not step:
            return None
        return StudyStepSchema.model_validate(step)

    async def get_step_with_navigation(self, step_id: uuid.UUID) -> Optional[StudyStepNavigationSchema]:
        current_step = await self.repo.get(step_id)
        if not current_step:
            return None

        next_step = await self.repo.get_next_ordered_instance(current_step, full_entity=True)
        response_dto = StudyStepNavigationSchema.model_validate(current_step)

        if next_step is None:
            response_dto.next = None
        else:
            assert type(next_step) is StudyStep
            response_dto.next = next_step.path

        return response_dto

    async def get_first_study_step(self, study_id: uuid.UUID) -> Optional[StudyStepSchema]:
        study_step = await self.repo.get_first_ordered_instance(study_id)
        if not study_step:
            return None
        return StudyStepSchema.model_validate(study_step)

    async def get_study_steps(self, study_id: uuid.UUID) -> list[StudyStepSchema]:
        step_objs = await self.repo.get_all_by_field('study_id', study_id)
        if step_objs:
            return [StudyStepSchema.model_validate(step) for step in step_objs]
        return []

    async def get_study_steps_as_ordered_list_Items(self, study_id: uuid.UUID) -> list[OrderedListItem]:
        step_objs = await self.get_study_steps(study_id)
        ordered_list_items = sorted(step_objs, key=lambda x: x.order_position)
        return [OrderedListItem.model_validate(oli) for oli in ordered_list_items]

    async def reorder_study_steps(self, study_id: uuid.UUID, steps_map: dict[uuid.UUID, int]) -> None:
        await self.repo.reorder_ordered_instances(study_id, steps_map)

    async def validate_step_path_uniqueness(
        self, study_id: uuid.UUID, path: str, exclude_step_id: Optional[uuid.UUID] = None
    ) -> bool:
        return await self.repo.validate_path_uniqueness(study_id, path, exclude_step_id)

    async def delete_step(self, step_id: uuid.UUID) -> None:
        await self.repo.delete_ordered_instance(step_id)

    async def get_next_step(self, step_id: uuid.UUID) -> Optional[StudyStepSchema]:
        current_step = await self.repo.get(step_id)
        if not current_step:
            return None
        next_step = await self.repo.get_next_ordered_instance(current_step, True)
        if not next_step:
            return None
        return StudyStepSchema.model_validate(next_step)
