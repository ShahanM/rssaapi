import uuid
from typing import Optional

from data.models.study_components import Study, User
from data.repositories.study import StudyRepository
from data.schemas.base_schemas import PreviewSchema
from data.schemas.study_components import ConditionCountSchema, StudySchema
from data.utility import sa_obj_to_dict


class StudyService:
    def __init__(self, study_repo: StudyRepository):
        self.repo = study_repo

    async def create_new_study(self, name: str, description: str, current_user: User) -> None:
        study = Study(
            name=name,
            description=description,
            created_by_id=current_user.id,
            owner_id=current_user.id,
        )

        await self.repo.create(study)

    async def update_study(self, study_id: uuid.UUID, update_payload: dict[str, str]) -> None:
        await self.repo.update(study_id, update_payload)

    async def get_studies_for_user(
        self,
        user_id: Optional[uuid.UUID],
        limit: int,
        offset: int,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[PreviewSchema]:
        studies = await self.repo.get_studies_paginated(user_id, limit, offset, sort_by, sort_dir, search)
        study_previews = [PreviewSchema.model_validate(study) for study in studies]
        return study_previews

    async def count_studies_for_user(self, user_id: Optional[uuid.UUID], search: Optional[str] = None) -> int:
        return await self.repo.count_studies(user_id, search)

    async def get_study_info_for_user(
        self,
        study_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        condition_counts: Optional[list[ConditionCountSchema]] = None,
    ) -> Optional[StudySchema]:
        study_row = None
        if condition_counts:
            study_row = await self.repo.get_total_participants(study_id)
        else:
            study_row = await self.repo.get_detailed_study_object(user_id, study_id)

        if study_row is None:
            return study_row

        study_obj = study_row.Study
        owner_sub = study_row.owner_auth0_sub
        creator_sub = study_row.creator_auth0_sub

        study_data = sa_obj_to_dict(study_obj)
        study_data['owner'] = owner_sub
        study_data['created_by'] = creator_sub

        if condition_counts:
            total_participants_count = study_row.total_participants
            study_data['total_participants'] = total_participants_count
            study_data['participants_by_condition'] = condition_counts

        return StudySchema.model_validate(study_data)

    async def get_study_info(
        self, study_id: uuid.UUID, condition_counts: Optional[list[ConditionCountSchema]] = None
    ) -> Optional[StudySchema]:
        return await self.get_study_info_for_user(study_id, None, condition_counts)

    async def delete_study(self, study_id: uuid.UUID) -> None:
        await self.repo.delete(study_id)

    # async def export_study_config(self, study_id: uuid.UUID) -> Optional[StudyConfigSchema]:
    # 	study_details = await self.get_study_details(study_id)

    # 	if study_details:
    # 		study_config = {
    # 			'study_id': study_details.id,
    # 			'study_steps': [
    # 				{'name': step.name, '_id': step.id}
    # 				for step in sorted(study_details.steps, key=lambda s: s.order_position)
    # 			]
    # 			if study_details.steps
    # 			else [],
    # 			'conditions': {cond.name: cond.id for cond in study_details.conditions}
    # 			if study_details.conditions
    # 			else None,
    # 		}
    # 		return StudyConfigSchema.model_validate(study_config)
    # 	return None
