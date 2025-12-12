import uuid
from datetime import datetime, timezone
from typing import Union

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AccessLog(Base):
    __tablename__ = 'access_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth0_user = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

    def __init__(self, auth0_user: str, action: str, resource: str, resource_id: Union[str, None] = None):
        self.auth0_user = auth0_user
        self.action = action
        self.resource = resource
        self.resource_id = resource_id


async def log_access(
    db: AsyncSession, auth0user: str, action: str, resource: str, resource_id: Union[str, None] = None
) -> None:
    log = AccessLog(auth0_user=auth0user, action=action, resource=resource, resource_id=resource_id)
    db.add(log)
    await db.flush()
