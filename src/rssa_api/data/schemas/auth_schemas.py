# in a file like 'core/schemas.py'
from typing import List, Optional

from pydantic import BaseModel


class Auth0UserSchema(BaseModel):
    """Represents an authenticated user from an Auth0 JWT."""

    sub: str
    permissions: List[str] = []
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
