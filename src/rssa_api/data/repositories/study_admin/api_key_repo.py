"""Repository for API key operations."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_components import ApiKey
from rssa_api.data.repositories.base_repo import BaseRepository


class ApiKeyRepository(BaseRepository[ApiKey]):
    """Repository for ApiKey model.

    Attributes:
        db: The database session.
        model: The ApiKey model class.
    """

    # def __init__(self, db: AsyncSession):
    #     """Initialize the ApiKeyRepository.

    #     Args:
    #         db: The database session.
    #     """
    #     super().__init__(db, ApiKey)

    async def get_active_api_key_with_study(self, key_hash: str, study_id: uuid.UUID) -> Optional[ApiKey]:
        """Get an active API key by its hash and associated study ID.

        Args:
            key_hash: The hash of the API key.
            study_id: The UUID of the associated study.

        Returns:
            The ApiKey instance if found, else None.
        """
        query = select(ApiKey).join(ApiKey.study).where(ApiKey.is_active, ApiKey.study_id == study_id)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()
