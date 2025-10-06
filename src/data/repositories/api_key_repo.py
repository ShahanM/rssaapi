import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import ApiKey
from data.repositories.base_repo import BaseRepository


class ApiKeyRepository(BaseRepository[ApiKey]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ApiKey)

    async def get_active_api_key_with_study(self, key_hash: str, study_id: uuid.UUID) -> Optional[ApiKey]:
        query = select(ApiKey).join(ApiKey.study).where(ApiKey.is_active, ApiKey.study_id == study_id)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()
