"""Repository for managing Demographic entities in the database."""

import uuid
from typing import Any

from sqlalchemy import MergedResult, update
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_participants import Demographic
from rssa_api.data.repositories.base_repo import BaseRepository


class DemographicsRepository(BaseRepository[Demographic]):
    """Repository for managing Demographic entities in the database.

    Inherits from BaseRepository to provide CRUD operations for Demographic model.

    Attributes:
        db (AsyncSession): The asynchronous database session.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the DemographicsRepository with a database session.

        Args:
            db: The asynchronous database session.
        """
        super().__init__(db, Demographic)

    async def update_response(self, item_id: uuid.UUID, update_payload: dict[str, Any], client_version: int) -> bool:
        """Update a Demographic entry with optimistic concurrency control.

        Args:
            item_id: The UUID of the Demographic entry to update.
            update_payload: The fields to update with their new values.
            client_version: The version of the entry as known by the client.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        update_fields = {**update_payload, 'version': client_version + 1}
        update_stmt = (
            update(Demographic)
            .where(Demographic.id == item_id, Demographic.version == client_version)
            .values(**update_fields)
        )

        result = await self.db.execute(update_stmt)

        if isinstance(result, MergedResult):
            if result.rowcount == 1:
                await self.db.commit()
                return True

        await self.db.rollback()
        return False
