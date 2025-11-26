"""Base repository for participant responses."""

import uuid
from typing import Type, TypeVar

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.rssa_base_models import DBBaseParticipantResponseModel
from rssa_api.data.repositories.base_repo import BaseRepository

ModelType = TypeVar('ModelType', bound=DBBaseParticipantResponseModel)


class BaseParticipantResponseRepository(BaseRepository[ModelType]):
    """Base repository for participant responses.

    Inherits from BaseRepository to provide CRUD operations for participant response models.

    Attributes:
        db: The database session.
        model: The participant response model class.
    """

    async def update_response(self, instance_id: uuid.UUID, update_data: dict, client_version: int) -> bool:
        """Update a participant response with optimistic concurrency control.

        Args:
            instance_id: The UUID of the participant response to update.
            update_data: A dictionary of fields to update.
            client_version: The version number provided by the client.

        Returns:
            True if the update was successful, False if there was a version conflict.
        """
        update_fields = {**update_data, 'version': client_version + 1}
        update_stmt = (
            update(self.model)
            .where(self.model.id == instance_id, self.model.version == client_version)
            .values(**update_fields)
        )

        result = await self.db.execute(update_stmt)
        if result.rowcount == 1:  # type: ignore
            await self.db.flush()
            return True
        else:
            await self.db.rollback()
            return False
