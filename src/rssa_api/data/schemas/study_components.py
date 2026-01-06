import uuid
from datetime import datetime
from typing import ClassVar, Generic, Optional, TypeVar

from pydantic import AliasPath, BaseModel, Field, computed_field

from .base_schemas import (
    AuditMixin,
    BaseOrderedMixin,
    DBMixin,
    DisplayInfoMixin,
    DisplayNameMixin,
)
from .survey_components import SurveyItemRead, SurveyScaleLevelRead


class ConditionCountSchema(BaseModel):
    condition_id: uuid.UUID
    condition_name: str
    participant_count: int

T = TypeVar('T', bound=BaseModel)


class NavigationWrapper(BaseModel, Generic[T]):
    """Wrap any schema T with a navigation fields."""

    data: T

    next_id: Optional[uuid.UUID] = None
    next_path: Optional[str] = None


class StudyComponentBase(BaseModel):
    name: str
    description: str


class StudyParentMixin(BaseModel):
    study_id: uuid.UUID


class StudyMetaOverrideMixin(BaseModel):
    title: Optional[str] = None
    instructions: Optional[str] = None


# ==============================================================================
# Study conditions
# table: study_conditions
# model: StudyCondition
# ==============================================================================
class StudyConditionBase(StudyComponentBase):
    recommendation_count: int
    recommender_key: Optional[str] = None
    created_by_id: Optional[uuid.UUID] = None
    pass


class StudyConditionCreate(StudyConditionBase):
    pass


class StudyConditionRead(StudyConditionBase, DBMixin, StudyParentMixin):
    pass


class StudyConditionAdminSchema(StudyConditionRead, AuditMixin):
    pass


# ==============================================================================
# Page content
# table: page_contents
# model: PageContent
# ==============================================================================
class StudyStepPageContentBase(BaseModel):
    survey_construct_id: uuid.UUID
    survey_scale_id: uuid.UUID
    preamble: Optional[str] = None


class StudyStepPageContentCreate(StudyStepPageContentBase):
    pass


class StudyStepPageContentUpdate(BaseModel):
    preamble: Optional[str] = None
    survey_construct_id: Optional[uuid.UUID] = None
    survey_scale_id: Optional[uuid.UUID] = None



class StudyStepPageContentRead(StudyStepPageContentBase, DBMixin, BaseOrderedMixin, DisplayNameMixin, DisplayInfoMixin):
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
    pass


# ==============================================================================
# StudyStepPages
# table: study_step_pages
# model: StudyStepPages
# ==============================================================================
class StudyStepPageBase(StudyComponentBase):
    page_type: Optional[str] = None


class StudyStepPageCreate(StudyStepPageBase):
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
    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'
    study_step_id: uuid.UUID

    study_step_page_contents: Optional[list[StudyStepPageContentRead]] = Field(
        validation_alias=AliasPath('study_step_page_contents'),
        default=[],
    )


class StudyStepPageAudit(StudyStepPageRead, AuditMixin):
    pass


# ==============================================================================
# Study steps
# table: study_step
# model: StudyStep
# ==============================================================================
class StudyStepBase(StudyComponentBase):
    step_type: Optional[str] = None

    path: str


class StudyStepCreate(StudyStepBase):
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
    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'

    survey_api_root: Optional[str] = None  # Deprecated, use root_page_info instead
    root_page_info: Optional[NavigationWrapper[StudyStepPageRead]] = None


class StudyStepAudit(StudyStepBase, AuditMixin):
    pass


# ==============================================================================
# Studies
# table: studies
# model: Study
# ==============================================================================
class StudyBase(StudyComponentBase):
    pass


class StudyCreate(StudyBase):
    pass


class StudyRead(StudyBase, DBMixin, DisplayNameMixin, DisplayInfoMixin):
    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'


class StudyAudit(StudyRead, AuditMixin):
    owner_id: Optional[uuid.UUID] = Field(
        None,  # Default value for an optional field
        description="""The owner's transformed identifier, used for querying
		the OAuth provider's API.""",
    )

    total_participants: Optional[int] = None
    participants_by_condition: Optional[list[ConditionCountSchema]] = None


# ==============================================================================
# Api keys
# table: api_keys
# model: ApiKey
# ==============================================================================
class ApiKeyBase(BaseModel):
    description: str


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyRead(ApiKeyBase, DBMixin, DisplayNameMixin, DisplayInfoMixin):
    _display_name_source_field: ClassVar[str] = 'plain_text_key'
    _display_info_source_field: ClassVar[str] = 'description'

    plain_text_key: str

    study_id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool

    created_at: datetime
    last_used_at: Optional[datetime] = None

    @computed_field
    @property
    def updated_at(self) -> Optional[datetime]:
        return self.last_used_at



