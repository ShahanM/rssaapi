import uuid
from typing import Optional

from rssa_api.data.models.study_components import (
    Study,
    StudyCondition,
    StudyStep,
    StudyStepPage,
    StudyStepPageContent,
    User,
)
from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.repositories.study_components import (
    StudyConditionRepository,
    StudyRepository,
    StudyStepPageContentRepository,
    StudyStepPageRepository,
    StudyStepRepository,
)
from rssa_api.data.repositories.study_participants import StudyParticipantRepository
from rssa_api.data.schemas.study_components import ConditionCountSchema
from datetime import datetime, timezone
from typing import Any

from rssa_api.data.models.study_participants import Demographic, ParticipantRecommendationContext
from rssa_api.data.repositories.study_participants import (
    ParticipantDemographicRepository,
    ParticipantRecommendationContextRepository,
)
from rssa_api.data.schemas.participant_schemas import DemographicsCreate
from rssa_api.data.schemas.preferences_schemas import RecommendationContextBaseSchema, RecommendationContextSchema
from rssa_api.data.services.base_ordered_service import BaseOrderedService
from rssa_api.data.services.base_scoped_service import BaseScopedService
from rssa_api.data.services.navigation_mixin import NavigationMixin


class StudyService(BaseScopedService[Study, StudyRepository]):
    """Service for managing studies."""

    scope_field = 'owner_id'


class StudyConditionService(BaseScopedService[StudyCondition, StudyConditionRepository]):
    """Service for managing study conditions."""

    scope_field = 'study_id'

    async def get_participant_count_by_condition(
        self,
        study_id: uuid.UUID,
    ) -> list[ConditionCountSchema]:
        """Get participant counts grouped by study conditions for a specific study."""
        condition_count_rows = await self.repo.get_participant_count_by_condition(study_id)

        participants_by_condition_list = []
        for row in condition_count_rows:
            participants_by_condition_list.append(
                ConditionCountSchema(
                    condition_id=row.study_condition_id,
                    condition_name=row.study_condition_name,
                    participant_count=row.participant_count,
                )
            )
        return participants_by_condition_list


class StudyStepService(
    BaseOrderedService[StudyStep, StudyStepRepository],
    NavigationMixin[StudyStep, StudyStepRepository],
):
    """Service for managing study steps."""

    scope_field = 'study_id'

    async def validate_step_path_uniqueness(
        self, study_id: uuid.UUID, path: str, exclude_step_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Validate that a study step path is unique within a study.

        Args:
            study_id: The ID of the study.
            path: The path to validate.
            exclude_step_id: An optional step ID to exclude from the uniqueness check.

        Returns:
            True if the path is unique, False otherwise.
        """
        return await self.repo.validate_path_uniqueness(study_id, path, exclude_step_id)


class StudyStepPageService(
    BaseOrderedService[StudyStepPage, StudyStepPageRepository],
    NavigationMixin[StudyStepPage, StudyStepPageRepository],
):
    """Service for managing study step pages."""

    scope_field = 'study_step_id'


class StudyStepPageContentService(BaseOrderedService[StudyStepPageContent, StudyStepPageContentRepository]):
    """Service for managing study step page content."""

    scope_field = 'study_step_page_id'


class StudyParticipantService(BaseScopedService[StudyParticipant, StudyParticipantRepository]):
    """Service for managing study participants."""

    scope_field = 'study_id'

    def __init__(
        self,
        participant_repo: StudyParticipantRepository,
        demographics_repo: ParticipantDemographicRepository,
        recommendation_context_repo: ParticipantRecommendationContextRepository,
    ):
        super().__init__(participant_repo)
        self.demographics_repo = demographics_repo
        self.recommendation_context_repo = recommendation_context_repo

    async def create_demographic_info(
        self, participant_id: uuid.UUID, demographic_data: DemographicsCreate
    ) -> DemographicsCreate:
        demographic_obj = Demographic(
            study_participant_id=participant_id,
            age_range=demographic_data.age_range,
            gender=demographic_data.gender,
            gender_other=demographic_data.gender_other,
            race=';'.join(demographic_data.race),
            race_other=demographic_data.race_other,
            education=demographic_data.education,
            country=demographic_data.country,
            state_region=demographic_data.state_region,
            updated_at=datetime.now(timezone.utc),
            version=1,
        )
        await self.demographics_repo.create(demographic_obj)

        return DemographicsCreate.model_validate(demographic_obj)

    async def update_demographic_info(
        self, demographics_id: uuid.UUID, update_data: dict[str, Any], client_version: int
    ) -> bool:
        return await self.demographics_repo.update_response(demographics_id, update_data, client_version)

    async def create_recommendation_context(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, context_data: RecommendationContextBaseSchema
    ) -> RecommendationContextSchema:
        from rssa_api.data.utility import convert_datetime_to_str, convert_uuids_to_str

        raw_dict = context_data.recommendations_json.model_dump()
        json_safe_dict = convert_uuids_to_str(raw_dict)
        json_safe_dict = convert_datetime_to_str(json_safe_dict)
        rec_ctx = ParticipantRecommendationContext(
            study_id=study_id,
            step_id=context_data.step_id,
            step_page_id=context_data.step_page_id,
            participant_id=participant_id,
            context_tag=context_data.context_tag,
            recommendations_json=json_safe_dict,
        )
        await self.recommendation_context_repo.create(rec_ctx)

        return RecommendationContextSchema.model_validate(rec_ctx)

    async def get_recommndation_context_by_participant_context(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, context_tag: str
    ) -> Optional[RecommendationContextSchema]:
        rec_ctx = await self.recommendation_context_repo.get_by_fields(
            [('study_id', study_id), ('participant_id', participant_id), ('context_tag', context_tag)]
        )

        if not rec_ctx:
            return None

        return RecommendationContextSchema.model_validate(rec_ctx)
