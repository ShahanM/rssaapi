"""Base schemas and mixins for database models and API responses."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, computed_field


class DBMixin(BaseModel):
    """A mixin that provides database-related fields."""

    id: uuid.UUID = Field(..., description='Unique identifier for the resource.')

    model_config = ConfigDict(
        from_attributes=True,
        # json_encoders={
        #     uuid.UUID: lambda v: str(v),
        #     datetime: lambda v: v.isoformat(),
        # },
    )


class AuditMixin(BaseModel):
    """A mixin that provides admin-related fields."""

    created_at: datetime | None = Field(
        ...,
        description='This is the timestamp logged at database insertion.',
    )
    updated_at: datetime | None = Field(..., description='This is the timestamp logged during last update.')


class DisplayNameMixin:
    """A mixin that provides a `display_name` computed field.

    Any class using this mixin MUST define a class variable
    `_display_name_source_field` which holds the name of the field
    to use as the source for the display name.
    """

    _display_name_source_field: ClassVar[str]

    @computed_field
    @property
    def display_name(self) -> str:
        """Get the display name from the source field."""
        return getattr(self, self._display_name_source_field)


class DisplayInfoMixin:
    """A mixin that provides a `display_info` computed field.

    Any class using this mixin MUST define a class variable
    `_display_info_source_field` which holds the name of the field
    to use as the source for the display name.
    """

    _display_info_source_field: ClassVar[str]

    @computed_field
    @property
    def display_info(self) -> str:
        """Get the display info from the source field."""
        return getattr(self, self._display_info_source_field)


class SortDir(str, Enum):
    """Enumeration for sort directions."""

    ASC = 'asc'
    DESC = 'desc'


class PreviewSchema(DBMixin, AuditMixin):
    """A schema for previewing resources with minimal information.

    _display_name_source_field: ClassVar[str] = 'name'
    _display_name_source_field: ClassVar[str] = 'name'
    """

    name: str


class BaseOrderedMixin(BaseModel):
    """A mixin that provides ordering capabilities."""

    order_position: int


class ReorderPayloadSchema(BaseOrderedMixin, DBMixin):
    """A schema for reordering items in a list."""

    pass


class OrderedListItem(DisplayNameMixin, ReorderPayloadSchema):
    """An ordered list item with a name."""

    _display_name_source_field: ClassVar[str] = 'name'
    name: str


class OrderedTextListItem(DisplayNameMixin, ReorderPayloadSchema):
    """An ordered list item with text."""

    _display_name_source_field: ClassVar[str] = 'text'
    text: str


class UpdatePayloadSchema(BaseModel):
    """A schema for updating resource fields."""

    parent_id: uuid.UUID
    updated_fields: dict[str, Any]


class VersionMixin(BaseModel):
    """A mixin that provides versioning capabilities."""

    version: int
