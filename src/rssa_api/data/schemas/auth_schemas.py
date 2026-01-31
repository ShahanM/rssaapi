"""Authentication related schemas."""

# in a file like 'core/schemas.py'
import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class Auth0UserSchema(BaseModel):
    """Represents an authenticated user from an Auth0 JWT."""

    sub: str
    permissions: list[str] = []
    email: str | None = None
    name: str | None = None
    picture: str | None = None


class UserSchema(BaseModel):
    """Schema for a User."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    auth0_sub: str
    email: str | None = None
    name: str | None = Field(default=None, validation_alias='desc')
    picture: str | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    # studies_owned: list[Any] = []
    # studies_created: list[Any] = []

    # api_keys: list[Any] = []
