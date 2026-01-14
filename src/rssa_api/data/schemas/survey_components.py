"""Schemas for survey components such as constructs, scales, items, and scale levels."""

import uuid
from typing import ClassVar

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
    """Schema for creating a survey scale level."""

    pass


class SurveyScaleLevelRead(SurveyScaleLevelBase, BaseOrderedMixin, DBMixin, DisplayNameMixin):
    """Schema for reading a survey scale level."""

    _display_name_source_field: ClassVar[str] = 'label'


class SurveyScaleLevelAudit(SurveyScaleLevelRead, AuditMixin):
    """Schema for auditing a survey scale level."""

    pass


# ==============================================================================
# Survey items
# table: survey_items
# model: SurveyItem
# ==============================================================================
class SurveyItemBase(BaseModel):
    """Base schema for survey item."""

    text: str
    survey_construct_id: uuid.UUID


class SurveyItemCreate(SurveyItemBase):
    """Schema for creating a survey item."""

    pass


class SurveyItemRead(SurveyItemBase, DBMixin, BaseOrderedMixin, DisplayNameMixin):
    """Schema for reading a survey item."""

    _display_name_source_field: ClassVar[str] = 'text'


class SurveyItemAudit(SurveyItemRead, AuditMixin):
    """Schema for auditing a survey item."""

    pass


# ==============================================================================
# Construct scales
# table: construct_scales
# model: ConstructScale
# ==============================================================================
class SurveyScaleBase(BaseModel):
    """Base schema for survey scale."""

    name: str | None = None
    description: str | None = None


class SurveyScaleCreate(SurveyScaleBase):
    """Schema for creating a survey scale."""

    pass


class SurveyScaleRead(SurveyScaleBase, DBMixin, DisplayNameMixin):
    """Schema for reading a survey scale."""

    _display_name_source_field: ClassVar[str] = 'name'


class SurveyScaleAudit(SurveyScaleRead, AuditMixin):
    """Schema for auditing a survey scale."""

    pass


# ==============================================================================
# Constructs
# table: constructs
# model: Construct
# ==============================================================================
class SurveyConstructBase(BaseModel):
    """Base schema for survey construct."""

    name: str
    description: str


class SurveyConstructCreate(SurveyConstructBase):
    """Schema for creating a survey construct."""

    pass


class SurveyConstructRead(SurveyConstructBase, DBMixin, DisplayNameMixin, DisplayInfoMixin):
    """Schema for reading a survey construct."""

    _display_name_source_field: ClassVar[str] = 'name'
    _display_info_source_field: ClassVar[str] = 'description'


class SurveyConstructAudit(SurveyConstructRead, AuditMixin):
    """Schema for auditing a survey construct."""

    pass
