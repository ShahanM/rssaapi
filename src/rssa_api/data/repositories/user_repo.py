from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_components import User
from rssa_api.data.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
