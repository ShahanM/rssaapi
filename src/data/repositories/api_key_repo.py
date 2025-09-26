import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import ApiKey
from data.repositories.base_repo import BaseRepository


class ApiKeyRepository(BaseRepository[ApiKey]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ApiKey)

    # async def get_all_by_fields(self, conditions: list[tuple[str, Any]]) -> Sequence[ApiKey]:
    #     query = select(ApiKey)
    #     _conditions = []
    #     for col_name, col_value in conditions:
    #         column_attribute = getattr(ApiKey, col_name)
    #         _conditions.append(column_attribute == col_value)
    #     query = query.where(and_(*_conditions))
    #     results = await self.db.execute(query)
    #     return results.scalars().all()

    async def get_active_api_key_with_study(self, key_hash: str, study_id: uuid.UUID) -> Optional[ApiKey]:
        query = select(ApiKey).join(ApiKey.study).where(ApiKey.is_active, ApiKey.study_id == study_id)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()
