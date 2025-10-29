from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.models.participant_movie_sequence import PreShuffledMovieList
from rssa_api.data.repositories.base_repo import BaseRepository


class PreShuffledMovieRepository(BaseRepository[PreShuffledMovieList]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PreShuffledMovieList)

    async def get_all_shuffled_lists_by_subset(self, subset_desc: str) -> Optional[List[PreShuffledMovieList]]:
        query = select(PreShuffledMovieList).where(PreShuffledMovieList.subset_desc == subset_desc)

        db_rows = await self.db.execute(query)
        return list(db_rows.scalars().all())
