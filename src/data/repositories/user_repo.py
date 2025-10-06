from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import User
from data.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
