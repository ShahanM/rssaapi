import uuid
from typing import Type, TypeVar

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.rssa_base_models import DBBaseParticipantResponseModel
from data.repositories.base_repo import BaseRepository

ModelType = TypeVar('ModelType', bound=DBBaseParticipantResponseModel)


class BaseParticipantResponseRepository(BaseRepository[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        super().__init__(db, model)

    async def update_response(self, instance_id: uuid.UUID, update_data: dict, client_version: int) -> bool:
        update_fields = {**update_data, 'version': client_version + 1}
        update_stmt = (
            update(self.model)
            .where(self.model.id == instance_id, self.model.version == client_version)
            .values(**update_fields)
        )

        result = await self.db.execute(update_stmt)
        if result.rowcount == 1:
            await self.db.flush()
            return True
        else:
            await self.db.rollback()
            return False
