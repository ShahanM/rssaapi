import uuid
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field, computed_field


class BaseDBMixin(BaseModel):
    id: uuid.UUID = Field(..., description='Unique identifier for the resource.')

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }


class BaseAdminMixin(BaseModel):
    created_at: Optional[datetime] = Field(
        ...,
        description='This is the timestamp logged at database insertion.',
    )
    updated_at: Optional[datetime] = Field(..., description='This is the timestamp logged during last update.')
    created_by_id: Optional[uuid.UUID] = Field(..., description='Id of the user who created this resource instance.')


class DisplayNameMixin:
    """
    A mixin that provides a `display_name` computed field.

    Any class using this mixin MUST define a class variable
    `_display_name_source_field` which holds the name of the field
    to use as the source for the display name.
    """

    _display_name_source_field: ClassVar[str]

    @computed_field
    @property
    def display_name(self) -> str:
        return getattr(self, self._display_name_source_field)


class DisplayInfoMixin:
    """
    A mixin that provides a `display_info` computed field.

    Any class using this mixin MUST define a class variable
    `_display_info_source_field` which holds the name of the field
    to use as the source for the display name.
    """

    _display_info_source_field: ClassVar[str]

    @computed_field
    @property
    def display_info(self) -> str:
        return getattr(self, self._display_info_source_field)


class SortDir(str, Enum):
    ASC = 'asc'
    DESC = 'desc'


class PreviewSchema(BaseDBMixin, BaseAdminMixin):
    name: str


class BaseOrderedMixin(BaseModel):
    order_position: int


class OrderedNavigationMixin(BaseOrderedMixin):
    next: Optional[uuid.UUID] = None


class ReorderPayloadSchema(BaseOrderedMixin, BaseDBMixin):
    pass


class OrderedListItem(DisplayNameMixin, ReorderPayloadSchema):
    _display_name_source_field: ClassVar[str] = 'name'
    name: str


class OrderedTextListItem(DisplayNameMixin, ReorderPayloadSchema):
    _display_name_source_field: ClassVar[str] = 'text'
    text: str


class UpdatePayloadSchema(BaseModel):
    parent_id: uuid.UUID
    updated_fields: dict[str, Any]


class VersionMixin(BaseModel):
    version: int
