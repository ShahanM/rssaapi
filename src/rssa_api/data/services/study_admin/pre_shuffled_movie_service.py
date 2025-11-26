import random
import uuid
from typing import List

from rssa_api.data.models.participant_movie_sequence import PreShuffledMovieList
from rssa_api.data.repositories.study_admin import PreShuffledMovieRepository


class PreShuffledMovieService:
    def __init__(self, shuffled_movie_repo: PreShuffledMovieRepository):
        self.shuffled_movie_repo = shuffled_movie_repo

    async def create_pre_shuffled_movie_list(
        self,
        movie_ids: List[uuid.UUID],
        subset: str,
        seed: int = 144,
    ) -> None:
        random.seed = seed
        random.shuffle(movie_ids)

        preshuffled_list = PreShuffledMovieList(movie_ids=movie_ids, subset=subset, seed=seed)

        await self.shuffled_movie_repo.create(preshuffled_list)
