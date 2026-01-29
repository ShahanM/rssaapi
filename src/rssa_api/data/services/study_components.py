"""Services for managing study components."""

import uuid
from datetime import UTC, datetime
from typing import Any

from rssa_storage.rssadb.models.study_components import (
    Study,
    StudyAuthorization,
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
    StudyAuthorizationRepository,
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

    def __init__(self, repo: StudyRepository, auth_repo: StudyAuthorizationRepository):
        """Initialize the study service."""
        super().__init__(repo)
        self.auth_repo = auth_repo

    async def check_study_access(self, study_id: uuid.UUID, user_id: uuid.UUID, min_role: str | None = None) -> bool:
        """Check if a user has access to a specific study with a minimum role.

        Roles hierarchy: owner > admin > editor > viewer.

        Args:
            study_id: The UUID of the study.
            user_id: The UUID of the user.
            min_role: The minimum role required ('admin', 'editor', 'viewer').

        Returns:
            True if the user has access and meets the role requirement, False otherwise.
        """
        roles_hierarchy = {'viewer': 0, 'editor': 1, 'admin': 2, 'owner': 3}
        min_level = roles_hierarchy.get(min_role, 0) if min_role else 0

        study = await self.repo.find_one(RepoQueryOptions(filters={'id': study_id}))
        if not study:
            return False

        auth_record = await self.auth_repo.find_one(
            RepoQueryOptions(filters={'study_id': study_id, 'user_id': user_id})
        )

        if not auth_record:
            return False

        user_level = roles_hierarchy.get(auth_record.role, 0)
        return user_level >= min_level

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
        """Get a paged list of studies the user is authorized to view."""
        options = RepoQueryOptions(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=(sort_dir == 'desc') if sort_dir else False,
            search_text=search,
            search_columns=getattr(self.repo, 'SEARCHABLE_COLUMNS', []),
        )

        items = await self.repo.get_authorized_for_user(user_id, options)

        if not schema:
            return list(items)
        return [schema.model_validate(item) for item in items]

    async def count_authorized_for_user(self, user_id: uuid.UUID, search: str | None = None) -> int:
        """Count studies authorized for a specific user."""
        return await self.repo.count_authorized_for_user(user_id, search)

    async def get_study_authorizations(self, study_id: uuid.UUID) -> list[StudyAuthorization]:
        """Get all authorizations for a study."""
        return await self.auth_repo.find_many(RepoQueryOptions(filters={'study_id': study_id}))

    async def add_study_authorization(self, study_id: uuid.UUID, user_id: uuid.UUID, role: str) -> StudyAuthorization:
        """Add authorization for a user to a study."""
        auth = StudyAuthorization(study_id=study_id, user_id=user_id, role=role)
        return await self.auth_repo.create(auth)

    async def remove_study_authorization(self, study_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Remove authorization for a user from a study."""
        existing = await self.auth_repo.find_one(RepoQueryOptions(filters={'study_id': study_id, 'user_id': user_id}))
        if existing:
            await self.auth_repo.delete(existing.id)


class StudyConditionService(BaseScopedService[StudyCondition, StudyConditionRepository]):
    """Service for managing study conditions."""

    scope_field = 'study_id'

    async def create_for_owner(self, owner_id: uuid.UUID, schema: Any, **kwargs) -> StudyCondition:
        """Create a study condition for an owner."""
        for _ in range(5):
            try:
                return await super().create_for_owner(owner_id, schema, **kwargs)
            except IntegrityError:
                continue

        existing_conditions = await self.get_all_for_owner(owner_id)
        existing_codes = {c.short_code for c in existing_conditions}

        short_code = generate_ref_code()

        for attempt_count in range(1, 102):
            if short_code not in existing_codes:
                break

            if attempt_count > 100:
                short_code = f'{short_code}-{attempt_count}'
                break

            short_code = generate_ref_code()

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
        """Initialize the study participant service."""
        super().__init__(participant_repo)
        self.demographics_repo = demographics_repo
        self.recommendation_context_repo = recommendation_context_repo

    async def get_participant_with_condition(self, participant_id: uuid.UUID) -> StudyParticipant | None:
        """Get a participant with their condition and type.

        Args:
            participant_id: The ID of the participant.

        Returns:
            The participant with their condition and type.
        """
        return await self.repo.find_one(
            RepoQueryOptions(
                ids=[participant_id],
                load_options=StudyParticipantRepository.LOAD_CONDITION_AND_TYPE,
            )
        )

    async def create_demographic_info(
        self, participant_id: uuid.UUID, demographic_data: DemographicsCreate
    ) -> DemographicsCreate:
        """Create demographic information for a participant.

        Args:
            participant_id: The UUID of the participant.
            demographic_data: The demographic data to create.

        Returns:
            The created demographic information.
        """
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
        """Update demographic information for a participant.

        Args:
            demographics_id: The UUID of the demographic information.
            update_data: The demographic data to update.
            client_version: The version of the client.

        Returns:
            True if the update was successful, False otherwise.
        """
        return await self.demographics_repo.update_response(demographics_id, update_data, client_version)

    async def create_recommendation_context(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, context_data: RecommendationContextBaseSchema
    ) -> RecommendationContextSchema:
        """Create recommendation context for a participant.

        Args:
            study_id: The UUID of the study.
            participant_id: The UUID of the participant.
            context_data: The recommendation context data to create.

        Returns:
            The created recommendation context.
        """
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
        """Get recommendation context for a participant.

        Args:
            study_id: The UUID of the study.
            participant_id: The UUID of the participant.
            context_tag: The context tag of the recommendation context.

        Returns:
            The recommendation context for the participant.
        """
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


class StudyAuthorizationService(BaseScopedService[StudyAuthorization, StudyAuthorizationRepository]):
    """Service for managing study authorizations."""

    scope_field = 'study_id'
