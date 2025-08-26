import random
import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant_movie_sequence import PreShuffledMovieList
from data.repositories.pre_shuffled_movie_list import PreShuffledMovieRepository


class ParticipantSessionService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.shuffled_movie_repo = PreShuffledMovieRepository(db)

	async def create_pre_shuffled_movie_list(self, movie_ids: List[uuid.UUID], subset: str, seed: int = 144) -> None:
		random.seed = seed
		random.shuffle(movie_ids)

		preshuffled_list = PreShuffledMovieList(movie_ids, subset, seed)

		await self.shuffled_movie_repo.create(preshuffled_list)
		await self.db.commit()
		await self.db.refresh(preshuffled_list)
