"""Services for managing study components."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends
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
    StudyAttentionCheckRepository,
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

from rssa_api.data.schemas.participant_schemas import DemographicsCreate
from rssa_api.data.schemas.preferences_schemas import RecommendationContextBaseSchema, RecommendationContextSchema
from rssa_api.data.schemas.study_components import ConditionCountSchema, NavigationWrapper
from rssa_api.data.services.base_ordered_service import BaseOrderedService
from rssa_api.data.services.base_scoped_service import BaseScopedService, SchemaType
from rssa_api.data.services.base_service import BaseService
from rssa_api.data.services.navigation_mixin import NavigationMixin
from rssa_api.data.sources.rssadb import get_service
from rssa_api.data.utility import extract_load_strategies


class StudyService(BaseService[Study, StudyRepository]):
    """Service for managing studies."""

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

        study = await self.repo.find_one(RepoQueryOptions(filters={'id': study_id}, load_columns=['id', 'owner_id']))
        if not study:
            return False

        if study.owner_id == user_id:
            return True

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
        top_cols, rel_map = extract_load_strategies(schema) if schema else (None, None)

        options = RepoQueryOptions(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=(sort_dir == 'desc') if sort_dir else False,
            search_text=search,
            search_columns=getattr(self.repo, 'SEARCHABLE_COLUMNS', []),
            load_columns=top_cols,
            load_relationships=rel_map,
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
        authorizations = await self.auth_repo.find_many(RepoQueryOptions(filters={'study_id': study_id}))
        return list(authorizations)

    async def add_study_authorization(self, study_id: uuid.UUID, user_id: uuid.UUID, role: str) -> StudyAuthorization:
        """Add authorization for a user to a study."""
        auth = StudyAuthorization(study_id=study_id, user_id=user_id, role=role)
        return await self.auth_repo.create(auth)

    async def remove_study_authorization(self, study_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Remove authorization for a user from a study."""
        existing = await self.auth_repo.find_one(
            RepoQueryOptions(filters={'study_id': study_id, 'user_id': user_id}, load_columns=['id'])
        )
        if existing:
            await self.auth_repo.delete(existing.id)


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

    def __init__(self, repo: StudyStepPageRepository, ac_repo: StudyAttentionCheckRepository):
        """Initialize the study service."""
        super().__init__(repo)
        self.ac_repo = ac_repo

    async def get_first_survey_page(
        self, step_id: uuid.UUID, schema: type[SchemaType]
    ) -> NavigationWrapper[SchemaType] | None:
        page = await self.get_first_with_navigation(step_id, schema)
        if not page:
            return None

        return NavigationWrapper[schema](
            data=schema.model_validate(page['current']), next_id=page['next_id'], next_path=page['next_path']
        )

    async def get_survey_page(
        self, page_id: uuid.UUID, schema: type[SchemaType]
    ) -> NavigationWrapper[SchemaType] | None:
        page = await self.get_with_navigation(page_id, schema)
        if not page:
            return None

        return NavigationWrapper[schema](
            data=schema.model_validate(page['current']), next_id=page['next_id'], next_path=page['next_path']
        )


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
        serialized_data = demographic_data.model_dump()

        # 2. Add your database-specific overrides
        serialized_data['study_participant_id'] = participant_id
        serialized_data['updated_at'] = datetime.now(UTC)
        serialized_data['version'] = 1

        # 3. Unpack directly into your SQLAlchemy model
        demographic_obj = Demographic(**serialized_data)

        # demographic_obj = Demographic(
        #     study_participant_id=participant_id,
        #     age_range=demographic_data.age_range,
        #     gender=demographic_data.gender,
        #     gender_other=demographic_data.gender_other,
        #     race=';'.join(demographic_data.race) if demographic_data.race else None,
        #     race_other=demographic_data.race_other,
        #     education=demographic_data.education,
        #     country=demographic_data.country,
        #     state_region=demographic_data.state_region,
        #     urbanicity=demographic_data.urbanicity,
        #     raw_json=demographic_data.raw_json,
        #     updated_at=datetime.now(UTC),
        #     version=1,
        # )
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


StudyServiceDep = Annotated[
    StudyService, Depends(get_service(StudyService, StudyRepository, StudyAuthorizationRepository))
]

StudyConditionServiceDep = Annotated[
    StudyConditionService,
    Depends(get_service(StudyConditionService, StudyConditionRepository)),
]

StudyStepServiceDep = Annotated[StudyStepService, Depends(get_service(StudyStepService, StudyStepRepository))]

StudyStepPageServiceDep = Annotated[
    StudyStepPageService,
    Depends(get_service(StudyStepPageService, StudyStepPageRepository, StudyAttentionCheckRepository)),
]

StudyStepPageContentServiceDep = Annotated[
    StudyStepPageContentService,
    Depends(get_service(StudyStepPageContentService, StudyStepPageContentRepository)),
]

StudyAuthorizationServiceDep = Annotated[
    StudyAuthorizationService,
    Depends(get_service(StudyAuthorizationService, StudyAuthorizationRepository)),
]

StudyParticipantServiceDep = Annotated[
    StudyParticipantService,
    Depends(
        get_service(
            StudyParticipantService,
            StudyParticipantRepository,
            ParticipantDemographicRepository,
            ParticipantRecommendationContextRepository,
        )
    ),
]
