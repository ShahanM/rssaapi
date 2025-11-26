import uuid
from typing import Optional

from rssa_api.data.models.study_components import StudyCondition
from rssa_api.data.repositories.study_components.study_condition import StudyConditionRepository
from rssa_api.data.schemas.study_components import ConditionCountSchema, StudyConditionBaseSchema, StudyConditionSchema


class StudyConditionService:
    def __init__(self, condition_repo: StudyConditionRepository):
        self.repo = condition_repo

    async def create_study_condition(self, study_id: uuid.UUID, new_condition: StudyConditionBaseSchema) -> None:
        study_condition = StudyCondition(
            name=new_condition.name,
            description=new_condition.description,
            study_id=study_id,
        )
        await self.repo.create(study_condition)

    async def get_study_conditions(self, study_id: uuid.UUID) -> list[StudyConditionSchema]:
        study_conditions = await self.repo.get_conditions_by_study_id(study_id)
        if len(study_conditions) > 0:
            return [StudyConditionSchema.model_validate(cond) for cond in study_conditions]
        return []

    async def get_study_condition(self, condition_id: uuid.UUID) -> Optional[StudyConditionSchema]:
        condition = await self.repo.get(condition_id)

        if not condition:
            return None

        return StudyConditionSchema.model_validate(condition)

    async def get_participant_count_per_coundition(self, study_id: uuid.UUID) -> list[ConditionCountSchema]:
        participants_by_condition_list = []
        condition_count_rows = await self.repo.get_participant_count_by_condition(study_id)

        for row in condition_count_rows:
            participants_by_condition_list.append(
                {
                    'condition_id': row.study_condition_id,
                    'condition_name': row.study_condition_name,
                    'participant_count': row.participant_count,
                }
            )
        return participants_by_condition_list
