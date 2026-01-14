# in a file like 'core/schemas.py'
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict


class Auth0UserSchema(BaseModel):
    """Represents an authenticated user from an Auth0 JWT."""

    sub: str
    permissions: list[str] = []
    email: str | None = None
    name: str | None = None
    picture: str | None = None


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    auth0_sub: str
    # studies_owned: list[Any] = []
    # studies_created: list[Any] = []

    # api_keys: list[Any] = []
