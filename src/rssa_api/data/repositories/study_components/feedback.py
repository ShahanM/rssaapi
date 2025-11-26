"""Repository for managing Feedback entities in the database."""

from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.participant_responses import Feedback
from rssa_api.data.repositories.base_repo import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    """Repository for managing Feedback entities in the database.

    Inherits from BaseRepository to provide CRUD operations for Feedback model.
    """

    pass
