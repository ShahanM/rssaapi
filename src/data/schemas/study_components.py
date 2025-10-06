import uuid
from datetime import datetime
from typing import ClassVar, Optional

from pydantic import AliasPath, BaseModel, Field, computed_field

from .analytics_schemas import ConditionCountSchema
from .base_schemas import (
    BaseAdminMixin,
    BaseDBMixin,
    BaseOrderedMixin,
    DisplayInfoMixin,
    DisplayNameMixin,
    OrderedNavigationMixin,
)
from .survey_constructs import ConstructItemSchema, ScaleLevelSchema


class StudyComponentBaseSchema(BaseModel):
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
class StudyConditionBaseSchema(StudyComponentBaseSchema):
    recommendation_count: int
    pass


class StudyConditionSchema(StudyConditionBaseSchema, BaseDBMixin, StudyParentMixin):
    pass


class StudyConditionAdminSchema(StudyConditionSchema, BaseAdminMixin):
    pass


# ==============================================================================
# Pages
# table: step_page
# model: Page
# ==============================================================================
class PageBaseSchema(StudyComponentBaseSchema):
    page_type: Optional[str] = None


class PageSchema(
    PageBaseSchema,
    BaseDBMixin,
    StudyParentMixin,
    BaseOrderedMixin,
    StudyMetaOverrideMixin,
    DisplayNameMixin,
    DisplayInfoMixin,
):
    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'
    step_id: uuid.UUID


class PageAdminSchema(PageSchema, BaseAdminMixin):
    pass


# ==============================================================================
# Study steps
# table: study_step
# model: StudyStep
# ==============================================================================
class StudyStepBaseSchema(StudyComponentBaseSchema):
    step_type: Optional[str] = None

    path: str


class StudyStepSchema(
    StudyStepBaseSchema,
    BaseDBMixin,
    StudyParentMixin,
    BaseOrderedMixin,
    StudyMetaOverrideMixin,
    DisplayNameMixin,
    DisplayInfoMixin,
):
    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'

    survey_api_root: Optional[str] = None


class StudyStepAdminSchema(StudyStepSchema, BaseAdminMixin):
    pass


class StudyStepNavigationSchema(StudyStepSchema):
    next: Optional[str] = None
    pass


# ==============================================================================
# Studies
# table: studies
# model: Study
# ==============================================================================
class StudyBaseSchema(StudyComponentBaseSchema):
    pass


class StudySchema(StudyBaseSchema, BaseDBMixin, DisplayNameMixin, DisplayInfoMixin):
    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'


class StudyAdminSchema(StudySchema, BaseAdminMixin):
    owner: Optional[str] = Field(
        None,  # Default value for an optional field
        description="""The owner's transformed identifier, used for querying
		the OAuth provider's API.""",
    )

    total_participants: Optional[int] = None
    participants_by_condition: Optional[list[ConditionCountSchema]] = None


# ==============================================================================
# Page content
# table: page_contents
# model: PageContent
# ==============================================================================
class PageContentBaseSchema(BaseModel):
    construct_id: uuid.UUID
    scale_id: uuid.UUID
    preamble: Optional[str] = None


class PageContentSchema(PageContentBaseSchema, BaseDBMixin, BaseOrderedMixin, DisplayNameMixin, DisplayInfoMixin):
    page_id: uuid.UUID

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'

    items: list[ConstructItemSchema] = Field(validation_alias=AliasPath('survey_construct', 'items'))

    name: str = Field(validation_alias=AliasPath('survey_construct', 'name'))
    description: str = Field(validation_alias=AliasPath('survey_construct', 'description'))

    scale_id: uuid.UUID = Field(validation_alias=AliasPath('construct_scale', 'id'))
    scale_name: str = Field(validation_alias=AliasPath('construct_scale', 'name'))
    scale_levels: list[ScaleLevelSchema] = Field(validation_alias=AliasPath('construct_scale', 'scale_levels'))


class PageContentAdminSchema(PageContentSchema, BaseAdminMixin):
    pass


# ==============================================================================
# Api keys
# table: api_keys
# model: ApiKey
# ==============================================================================
class ApiKeyBaseSchema(BaseModel):
    description: str


class ApiKeySchema(ApiKeyBaseSchema, BaseDBMixin, DisplayNameMixin, DisplayInfoMixin):
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


class PageNavigationSchema(PageSchema, OrderedNavigationMixin, StudyParentMixin):
    pass


class SurveyPage(PageNavigationSchema):
    page_content: list[PageContentSchema]
