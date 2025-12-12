"""Repository for pre-shuffled movie lists."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.participant_movie_sequence import PreShuffledMovieList
from rssa_api.data.repositories.base_repo import BaseRepository


class PreShuffledMovieRepository(BaseRepository[PreShuffledMovieList]):
    """Repository for PreShuffledMovieList model."""

    # def __init__(self, db: AsyncSession):
    #     """Initialize the PreShuffledMovieRepository.

    #     Args:
    #         db: The database session.
    #     """
    #     super().__init__(db, PreShuffledMovieList)

    async def get_all_shuffled_lists_by_subset(self, subset_desc: str) -> Optional[List[PreShuffledMovieList]]:
        """Get all pre-shuffled movie lists by subset description.

        Args:
            subset_desc: The subset description to filter by.

        Returns:
            A list of PreShuffledMovieList instances if found, else None.
        """
        # query = select(PreShuffledMovieList).where(PreShuffledMovieList.subset_desc == subset_desc)
        # db_rows = await self.db.execute(query)
        # return list(db_rows.scalars().all())
        from rssa_api.data.repositories.base_repo import RepoQueryOptions
        return await self.find_many(RepoQueryOptions(filters={'subset_desc': subset_desc}))
