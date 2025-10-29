import uuid
from typing import ClassVar, Optional

from pydantic import BaseModel

from rssa_api.data.schemas.base_schemas import (
    BaseAdminMixin,
    BaseDBMixin,
    BaseOrderedMixin,
    DisplayInfoMixin,
    DisplayNameMixin,
)


# ==============================================================================
# Scale levels
# table: scale_levels
# model: ScaleLevel
# ==============================================================================
class ScaleLevelBaseSchema(BaseModel):
    scale_id: uuid.UUID
    value: int
    label: str


class ScaleLevelSchema(ScaleLevelBaseSchema, BaseOrderedMixin, BaseDBMixin, DisplayNameMixin):
    _display_name_source_field: ClassVar[str] = 'label'


class ScaleLevelAdminSchema(ScaleLevelSchema, BaseAdminMixin):
    pass


# ==============================================================================
# Construct items
# table: construct_items
# model: Constructitem
# ==============================================================================
class ConstructItemBaseSchema(BaseModel):
    text: str
    construct_id: uuid.UUID


class ConstructItemSchema(ConstructItemBaseSchema, BaseDBMixin, BaseOrderedMixin, DisplayNameMixin):
    _display_name_source_field: ClassVar[str] = 'text'


class ConstructItemAdminSchema(ConstructItemSchema, BaseAdminMixin):
    pass


# ==============================================================================
# Construct scales
# table: construct_scales
# model: ConstructScale
# ==============================================================================
class ConstructScaleBaseSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ConstructScaleSchema(ConstructScaleBaseSchema, BaseDBMixin, DisplayNameMixin):
    _display_name_source_field: ClassVar[str] = 'name'


class ConstructScaleAdminSchema(ConstructScaleSchema, BaseAdminMixin):
    pass


# ==============================================================================
# Constructs
# table: constructs
# model: Construct
# ==============================================================================
class ConstructBaseSchema(BaseModel):
    name: str
    description: str


class SurveyConstructSchema(ConstructBaseSchema, BaseDBMixin, DisplayNameMixin, DisplayInfoMixin):
    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'


class SurveyConstructAdminSchema(SurveyConstructSchema, BaseAdminMixin):
    pass
