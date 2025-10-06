import uuid
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_participants import Demographic
from data.repositories.base_repo import BaseRepository


class DemographicsRepository(BaseRepository[Demographic]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Demographic)

    async def update_response(self, item_id: uuid.UUID, update_payload: dict[str, Any], client_version: int) -> bool:
        update_fields = {**update_payload, 'version': client_version + 1}
        update_stmt = (
            update(Demographic)
            .where(Demographic.id == item_id, Demographic.version == client_version)
            .values(**update_fields)
        )

        result = await self.db.execute(update_stmt)

        if result.rowcount == 1:
            await self.db.commit()
            return True
        else:
            await self.db.rollback()
            return False
