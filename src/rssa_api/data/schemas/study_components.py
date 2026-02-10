"""Schemas for study components."""

import uuid
from datetime import datetime
from typing import ClassVar, Generic, TypeVar

from pydantic import AliasPath, BaseModel, ConfigDict, Field, computed_field

from .base_schemas import (
    AuditMixin,
    BaseOrderedMixin,
    DBMixin,
    DisplayInfoMixin,
    DisplayNameMixin,
    PreviewSchema,
)
from .survey_components import SurveyItemRead, SurveyScaleLevelRead


class PaginatedStudyResponse(BaseModel):
    """Schema for a paginated list of studies."""

    rows: list[PreviewSchema]  # type: ignore
    page_count: int

    model_config = ConfigDict(from_attributes=True)


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
    created_by_id: uuid.UUID | None = None
    authorized_test_code: str | None = None
    pass


class StudyConditionCreate(StudyConditionBase):
    """Schema for creating a study condition."""

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
# Page content
# table: page_contents
# model: PageContent
# ==============================================================================
class StudyStepPageContentBase(BaseModel):
    """Base schema for study step page content."""

    survey_construct_id: uuid.UUID
    survey_scale_id: uuid.UUID
    preamble: str | None = None


class StudyStepPageContentCreate(StudyStepPageContentBase):
    """Schema for creating study step page content."""

    pass


class StudyStepPageContentUpdate(BaseModel):
    """Schema for updating study step page content."""

    preamble: str | None = None
    survey_construct_id: uuid.UUID | None = None
    survey_scale_id: uuid.UUID | None = None


class StudyStepPageContentRead(StudyStepPageContentBase, DBMixin, BaseOrderedMixin, DisplayNameMixin, DisplayInfoMixin):
    """Schema for reading study step page content."""

    study_step_page_id: uuid.UUID

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'

    items: list[SurveyItemRead] = Field(validation_alias=AliasPath('survey_construct', 'survey_items'))

    name: str = Field(validation_alias=AliasPath('survey_construct', 'name'))
    description: str = Field(validation_alias=AliasPath('survey_construct', 'description'))

    scale_id: uuid.UUID = Field(validation_alias=AliasPath('survey_scale', 'id'))
    scale_name: str = Field(validation_alias=AliasPath('survey_scale', 'name'))
    scale_levels: list[SurveyScaleLevelRead] = Field(validation_alias=AliasPath('survey_scale', 'survey_scale_levels'))


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

    pass


class StudyStepPageRead(
    StudyStepPageBase,
    DBMixin,
    StudyParentMixin,
    BaseOrderedMixin,
    StudyMetaOverrideMixin,
    DisplayNameMixin,
    DisplayInfoMixin,
):
    """Schema for reading study step page."""

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'
    study_step_id: uuid.UUID

    study_step_page_contents: list[StudyStepPageContentRead] | None = Field(
        validation_alias=AliasPath('study_step_page_contents'),
        default=[],
    )


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

    pass


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

    pass


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
