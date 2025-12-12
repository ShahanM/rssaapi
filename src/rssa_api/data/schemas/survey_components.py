"""Schemas for survey components such as constructs, scales, items, and scale levels."""

import uuid
from typing import ClassVar, Optional

from pydantic import BaseModel

from rssa_api.data.schemas.base_schemas import (
    AuditMixin,
    BaseOrderedMixin,
    DBMixin,
    DisplayInfoMixin,
    DisplayNameMixin,
)


# ==============================================================================
# Scale levels
# table: survey_scale_levels
# model: SurveyScaleLevel
# ==============================================================================
class SurveyScaleLevelBase(BaseModel):
    """Base schema for survey scale levels."""

    survey_scale_id: uuid.UUID
    value: int
    label: str


class SurveyScaleLevelCreate(SurveyScaleLevelBase):
    pass


class SurveyScaleLevelRead(SurveyScaleLevelBase, BaseOrderedMixin, DBMixin, DisplayNameMixin):
    _display_name_source_field: ClassVar[str] = 'label'


class SurveyScaleLevelAudit(SurveyScaleLevelRead, AuditMixin):
    pass


# ==============================================================================
# Survey items
# table: survey_items
# model: SurveyItem
# ==============================================================================
class SurveyItemBase(BaseModel):
    text: str
    survey_construct_id: uuid.UUID


class SurveyItemCreate(SurveyItemBase):
    pass


class SurveyItemRead(SurveyItemBase, DBMixin, BaseOrderedMixin, DisplayNameMixin):
    _display_name_source_field: ClassVar[str] = 'text'


class SurveyItemAudit(SurveyItemRead, AuditMixin):
    pass


# ==============================================================================
# Construct scales
# table: construct_scales
# model: ConstructScale
# ==============================================================================
class SurveyScaleBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SurveyScaleCreate(SurveyScaleBase):
    pass


class SurveyScaleRead(SurveyScaleBase, DBMixin, DisplayNameMixin):
    _display_name_source_field: ClassVar[str] = 'name'


class SurveyScaleAudit(SurveyScaleRead, AuditMixin):
    pass


# ==============================================================================
# Constructs
# table: constructs
# model: Construct
# ==============================================================================
class SurveyConstructBase(BaseModel):
    name: str
    description: str


class SurveyConstructCreate(SurveyConstructBase):
    pass


class SurveyConstructRead(SurveyConstructBase, DBMixin, DisplayNameMixin, DisplayInfoMixin):
    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'


class SurveyConstructAudit(SurveyConstructRead, AuditMixin):
    pass
