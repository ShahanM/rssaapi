"""Repository for user operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.study_components import User
from rssa_api.data.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model.

    Attributes:
        db: The database session.
        model: The User model class.
    """

    pass
    # def __init__(self, db: AsyncSession):
    #     """Initialize the UserRepository.

    #     Args:
    #         db: The database session.
    #     """
    #     super().__init__(db, User)
