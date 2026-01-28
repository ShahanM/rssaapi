import uuid
from datetime import UTC, datetime
from typing import Any

from rssa_storage.rssadb.models.study_components import (
    Study,
    StudyCondition,
    StudyStep,
    StudyStepPage,
    StudyStepPageContent,
)
from rssa_storage.rssadb.models.study_participants import (
    Demographic,
    ParticipantRecommendationContext,
    StudyParticipant,
)
from rssa_storage.rssadb.repositories.study_components import (
    StudyConditionRepository,
    StudyRepository,
    StudyStepPageContentRepository,
    StudyStepPageRepository,
    StudyStepRepository,
)
from rssa_storage.rssadb.repositories.study_participants import (
    ParticipantDemographicRepository,
    ParticipantRecommendationContextRepository,
    StudyParticipantRepository,
)
from rssa_storage.shared import RepoQueryOptions
from rssa_storage.shared.generators import generate_ref_code
from sqlalchemy.exc import IntegrityError

from rssa_api.data.schemas.participant_schemas import DemographicsCreate
from rssa_api.data.schemas.preferences_schemas import RecommendationContextBaseSchema, RecommendationContextSchema
from rssa_api.data.schemas.study_components import ConditionCountSchema
from rssa_api.data.services.base_ordered_service import BaseOrderedService
from rssa_api.data.services.base_scoped_service import BaseScopedService
from rssa_api.data.services.navigation_mixin import NavigationMixin


class StudyService(BaseScopedService[Study, StudyRepository]):
    """Service for managing studies."""

    scope_field = 'owner_id'

    async def check_study_access(self, study_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if a user has access to a specific study.

        Args:
            study_id: The UUID of the study.
            user_id: The UUID of the user.

        Returns:
            True if the user has access, False otherwise.
        """
        # FUTURE: Implement join table check here (e.g. study_permissions)
        # For now, we check ownership which is the current source of truth.
        study = await self.repo.find_one(RepoQueryOptions(filters={'id': study_id}))
        if not study:
            return False

        return study.owner_id == user_id

    async def get_paged_for_authorized_user(
        self,
        user_id: uuid.UUID,
        limit: int,
        offset: int,
        schema: Any | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        search: str | None = None,
    ) -> list[Any]:
        """Get a paged list of studies the user is authorized to view.

        This wraps get_paged_for_owner for now but allows for future expansion
        to include shared studies.
        """
        return await self.get_paged_for_owner(
            owner_id=user_id,
            limit=limit,
            offset=offset,
            schema=schema,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
        )


class StudyConditionService(BaseScopedService[StudyCondition, StudyConditionRepository]):
    """Service for managing study conditions."""

    scope_field = 'study_id'

    async def create_for_owner(self, owner_id: uuid.UUID, schema: Any, **kwargs) -> StudyCondition:
        # Optimistic Phase: Try to create using model default
        for _ in range(5):
            try:
                return await super().create_for_owner(owner_id, schema, **kwargs)
            except IntegrityError:
                continue

        # Fallback Phase: Manual Generation
        # 1. Fetch all existing conditions for this study (owner)
        existing_conditions = await self.get_all_for_owner(owner_id)
        existing_codes = {c.short_code for c in existing_conditions}

        # 2. Attempt to generate a unique code
        short_code = generate_ref_code()

        # Retry up to 100 times
        for attempt_count in range(1, 102):
            if short_code not in existing_codes:
                break

            # If we exceeded 100 attempts, use the fallback
            if attempt_count > 100:
                short_code = f'{short_code}-{attempt_count}'
                break

            short_code = generate_ref_code()

        # 3. Inject into kwargs and Create
        kwargs['short_code'] = short_code
        return await super().create_for_owner(owner_id, schema, **kwargs)

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
        self, study_id: uuid.UUID, path: str, exclude_step_id: uuid.UUID | None = None
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

    async def get_participant_with_condition(self, participant_id: uuid.UUID) -> StudyParticipant | None:
        return await self.repo.find_one(
            RepoQueryOptions(
                ids=[participant_id],
                load_options=StudyParticipantRepository.LOAD_CONDITION_AND_TYPE,
            )
        )

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
            updated_at=datetime.now(UTC),
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
            study_step_id=context_data.step_id,
            study_step_page_id=context_data.step_page_id,
            study_participant_id=participant_id,
            context_tag=context_data.context_tag,
            recommendations_json=json_safe_dict,
        )
        await self.recommendation_context_repo.create(rec_ctx)

        return RecommendationContextSchema.model_validate(rec_ctx)

    async def get_recommndation_context_by_participant_context(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, context_tag: str
    ) -> RecommendationContextSchema | None:
        rec_ctx = await self.recommendation_context_repo.find_many(
            RepoQueryOptions(
                filters={
                    'study_id': study_id,
                    'participant_id': participant_id,
                    'context_tag': context_tag,
                }
            )
        )

        if not rec_ctx:
            return None

        return RecommendationContextSchema.model_validate(rec_ctx)
