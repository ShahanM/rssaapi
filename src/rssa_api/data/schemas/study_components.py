"""Schemas for study components."""

import uuid
from datetime import datetime
from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel, Field, computed_field

from .base_schemas import (
    AuditMixin,
    BaseOrderedMixin,
    DBMixin,
    DisplayInfoMixin,
    DisplayNameMixin,
)
from .survey_components import (
    SurveyConstructPreview,
    SurveyConstructRead,
    SurveyItemRead,
    SurveyScaleLevelRead,
    SurveyScaleRead,
)


class ConditionCountSchema(BaseModel):
    """Schema for condition counts."""

    condition_id: uuid.UUID
    condition_name: str
    participant_count: int


T = TypeVar('T', bound=BaseModel)


class NavigationWrapper(BaseModel, Generic[T]):
    """Wrap any schema T with navigation fields."""

    """Wrap any schema T with a navigation fields."""

    data: T

    next_id: uuid.UUID | None = None
    next_path: str | None = None


class StudyComponentBase(BaseModel):
    """Base schema for study component."""

    name: str
    description: str


class StudyParentMixin(BaseModel):
    """Mixin for study parent."""

    study_id: uuid.UUID


class StudyMetaOverrideMixin(BaseModel):
    """Mixin for study metadata overrides."""

    title: str | None = None
    instructions: str | None = None


# ==============================================================================
# Study conditions
# table: study_conditions
# model: StudyCondition
# ==============================================================================
class StudyConditionBase(StudyComponentBase):
    """Base schema for study condition."""

    recommendation_count: int
    recommender_key: str | None = None
    view_link_key: str | None = None


class StudyConditionCreate(StudyConditionBase):
    """Schema for creating a study condition."""

    study_id: uuid.UUID


class StudyConditionPresent(StudyComponentBase, DBMixin):
    short_code: str
    view_link_key: str


class StudyConditionPreview(StudyComponentBase, DBMixin):
    pass


class StudyConditionRead(StudyConditionBase, DBMixin, StudyParentMixin):
    """Schema for reading a study condition."""

    enabled: bool
    short_code: str
    pass


class StudyConditionAdminSchema(StudyConditionRead, AuditMixin):
    """Schema for admin study condition."""

    pass


# ==============================================================================
# Study attention checks
# table: study_attention_checks
# model: StudyAttentionCheck
# ==============================================================================
class StudyAttentionCheckBase(BaseModel):
    """Base schema for the attention check blueprint."""

    text: str
    assigned_position: int
    study_step_id: uuid.UUID
    study_step_page_id: uuid.UUID
    study_step_page_content_id: uuid.UUID
    survey_scale_id: uuid.UUID
    expected_survey_scale_level_id: uuid.UUID


class StudyAttentionCheckCreate(StudyAttentionCheckBase):
    """Schema for creating a study attention check."""

    pass


class StudyAttentionCheckRead(StudyAttentionCheckBase, DBMixin, DisplayNameMixin):
    """Schema for reading a study attention check.

    Note: This is used internally for validation and hydration.
    When sent to the frontend, it is 'ghosted' into a SurveyItemRead
    via the StudyStepPageContentRead computed property.
    """

    _display_name_source_field: ClassVar[str] = 'text'

    pass


class StudyAttentionCheckAudit(StudyAttentionCheckRead, AuditMixin):
    """Schema for auditing an attention check."""

    pass


# ==============================================================================
# Page content
# table: page_contents
# model: PageContent
# ==============================================================================
class StudyStepPageContentBase(BaseModel):
    """Base schema for study step page content."""

    survey_construct_id: uuid.UUID
    survey_scale_id: uuid.UUID
    preamble: str | None = None


class StudyStepPageContentUpdate(BaseModel):
    """Schema for updating study step page content."""

    preamble: str | None = None
    survey_construct_id: uuid.UUID | None = None
    survey_scale_id: uuid.UUID | None = None


class StudyStepPageContentPreview(BaseOrderedMixin, DBMixin):
    """Schema for the study step page content which only shows the associated survey construct."""

    survey_construct: SurveyConstructPreview | None = None

    @computed_field
    @property
    def name(self) -> str:
        if self.survey_construct:
            return self.survey_construct.name
        return ''


class StudyStepPageContentRead(StudyStepPageContentBase, DBMixin, BaseOrderedMixin, DisplayNameMixin, DisplayInfoMixin):
    """Schema for reading study step page content."""

    study_step_page_id: uuid.UUID

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'

    survey_construct: SurveyConstructRead | None = None
    survey_scale: SurveyScaleRead | None = None

    study_attention_check: StudyAttentionCheckRead | None = None

    @computed_field
    @property
    def name(self) -> str:
        if self.survey_construct:
            return self.survey_construct.name
        return ''

    @computed_field
    @property
    def description(self) -> str:
        if self.survey_construct:
            return self.survey_construct.description
        return ''

    @computed_field
    @property
    def items(self) -> list[SurveyItemRead]:
        """Raw DB items only. Ignored by extract_load_strategies because it's a computed field."""
        item_list: list = []
        if self.survey_construct:
            item_list = self.survey_construct.survey_items
        if self.study_attention_check:
            item_list.insert(self.study_attention_check.assigned_position, self.study_attention_check)

        return item_list

    @computed_field
    @property
    def scale_id(self) -> uuid.UUID | None:
        if self.survey_scale:
            return self.survey_scale.id
        return None

    @computed_field
    @property
    def scale_name(self) -> str:
        if self.survey_scale and self.survey_scale.name:
            return self.survey_scale.name
        return ''

    @computed_field
    @property
    def scale_levels(self) -> list[SurveyScaleLevelRead]:
        if self.survey_scale and self.survey_scale.survey_scale_levels:
            return self.survey_scale.survey_scale_levels
        return []


class StudyStepPageContentPresent(StudyStepPageContentRead):
    """Used ONLY for the final FastAPI response."""

    pass
    # items: list[SurveyItemRead | ParticipantAttentionCheckResponseRead] = Field(default_factory=list)
    # @computed_field
    # @property
    # def items(self) -> list[SurveyItemRead | ParticipantAttentionCheckResponseRead]:
    #     if self.db_items and self.


class StudyStepPageContentAudit(StudyStepPageContentRead, AuditMixin):
    """Schema for auditing study step page content."""

    pass


# ==============================================================================
# StudyStepPages
# table: study_step_pages
# model: StudyStepPages
# ==============================================================================
class StudyStepPageBase(StudyComponentBase):
    """Base schema for study step page."""

    page_type: str | None = None


class StudyStepPageCreate(StudyStepPageBase):
    """Schema for creating study step page."""

    study_id: uuid.UUID
    study_step_id: uuid.UUID


class StudyStepPageRead(
    StudyStepPageBase,
    DBMixin,
    StudyParentMixin,
    BaseOrderedMixin,
    StudyMetaOverrideMixin,
    DisplayNameMixin,
    DisplayInfoMixin,
    Generic[T],
):
    """Schema for reading study step page."""

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'
    study_step_id: uuid.UUID

    study_step_page_contents: list[T] | None = None


class StudyStepPageReadAdmin(StudyStepPageRead[StudyStepPageContentPreview]):
    """Schema for the admin dashboard."""

    pass


class StudyStepPagePresent(StudyStepPageRead[StudyStepPageContentPresent]):
    study_step_page_contents: list[StudyStepPageContentPresent] | None = Field(default_factory=list)


class StudyStepPageAudit(StudyStepPageRead, AuditMixin):
    """Schema for auditing study step page."""

    pass


# ==============================================================================
# Study steps
# table: study_step
# model: StudyStep
# ==============================================================================
class StudyStepBase(StudyComponentBase):
    """Base schema for study step."""

    step_type: str | None = None
    path: str


class StudyStepCreate(StudyStepBase):
    """Schema for creating study step."""

    study_id: uuid.UUID


class StudyStepPreview(StudyStepBase, DBMixin, BaseOrderedMixin, DisplayNameMixin, DisplayInfoMixin):
    study_id: uuid.UUID


class StudyStepRead(
    StudyStepBase,
    DBMixin,
    StudyParentMixin,
    BaseOrderedMixin,
    StudyMetaOverrideMixin,
    DisplayNameMixin,
    DisplayInfoMixin,
):
    """Schema for reading study step."""

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'

    survey_api_root: str | None = None  # Deprecated, use root_page_info instead
    root_page_info: NavigationWrapper[StudyStepPageRead] | None = None


class StudyStepPresent(
    StudyStepBase,
    DBMixin,
    StudyParentMixin,
    BaseOrderedMixin,
    StudyMetaOverrideMixin,
    DisplayNameMixin,
    DisplayInfoMixin,
):
    """Schema for reading study step."""

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'

    survey_api_root: str | None = None  # Deprecated, use root_page_info instead
    root_page_info: NavigationWrapper[StudyStepPagePresent] | None = None


class StudyStepAudit(StudyStepBase, AuditMixin):
    """Schema for auditing study step."""

    pass


# ==============================================================================
# Studies
# table: studies
# model: Study
# ==============================================================================
class StudyBase(StudyComponentBase):
    """Base schema for study."""

    pass


class StudyCreate(StudyBase):
    """Schema for creating study."""

    pass


class StudyRead(StudyBase, DBMixin, DisplayNameMixin, DisplayInfoMixin):
    """Schema for reading study."""

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'

    completion_code: str | None = None
    redirect_url: str | None = None
    dataset_subset: str | None = None


class StudyAudit(StudyRead, AuditMixin):
    """Schema for auditing study."""

    owner_id: uuid.UUID | None = Field(
        None,  # Default value for an optional field
        description="""The owner's transformed identifier, used for querying
		the OAuth provider's API.""",
    )

    total_participants: int | None = None
    participants_by_condition: list[ConditionCountSchema] | None = None


# ==============================================================================
# Api keys
# table: api_keys
# model: ApiKey
# ==============================================================================
class ApiKeyBase(BaseModel):
    """Base schema for API key."""

    description: str


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating API key."""

    study_id: uuid.UUID
    user_id: uuid.UUID


class ApiKeyRead(ApiKeyBase, DBMixin, DisplayNameMixin, DisplayInfoMixin):
    """Schema for reading API key."""

    _display_name_source_field: ClassVar[str] = 'plain_text_key'
    _display_info_source_field: ClassVar[str] = 'description'

    plain_text_key: str

    study_id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool

    created_at: datetime
    last_used_at: datetime | None = None

    @computed_field
    @property
    def updated_at(self) -> datetime | None:
        """Return the last used at timestamp."""
        return self.last_used_at


# ==============================================================================
# Study Authorizations
# table: study_authorizations
# model: StudyAuthorization
# ==============================================================================
class StudyAuthorizationBase(BaseModel):
    """Base schema for study authorization."""

    user_id: uuid.UUID
    role: str = 'viewer'


class StudyAuthorizationCreate(StudyAuthorizationBase):
    """Schema for creating study authorization."""

    pass


class StudyAuthorizationRead(StudyAuthorizationBase, DBMixin, AuditMixin):
    """Schema for reading study authorization."""

    study_id: uuid.UUID
