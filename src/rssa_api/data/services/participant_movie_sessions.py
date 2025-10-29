import random
import uuid
from typing import Optional

from async_lru import alru_cache
from pydantic import BaseModel

from rssa_api.data.models.participant_movie_sequence import ParticipantMovieSession
from rssa_api.data.repositories.participant_movie_session import ParticipantMovieSessionRepository
from rssa_api.data.repositories.pre_shuffled_movie_list import PreShuffledMovieRepository


class PagedMoviesSchema(BaseModel):
    movies: list[uuid.UUID]
    total: int


class ParticipantMovieSessionService:
    def __init__(
        self,
        movie_session_repo: ParticipantMovieSessionRepository,
        shuffled_movie_repo: PreShuffledMovieRepository,
    ):
        self.movie_session_repo = movie_session_repo
        self.shuffled_movie_repo = shuffled_movie_repo

    @alru_cache(maxsize=128)
    async def get_next_session_movie_ids_batch(
        self, participant_id: uuid.UUID, offset: int, limit: int
    ) -> Optional[PagedMoviesSchema]:
        participant_assigned_list = await self.movie_session_repo.get_movie_session_by_participant_id(participant_id)
        if not participant_assigned_list:
            return None
        movie_ids = list(participant_assigned_list.assigned_list.movie_ids)

        paged_movie = {'movies': movie_ids[offset : min(offset + limit, len(movie_ids))], 'total': len(movie_ids)}

        return PagedMoviesSchema.model_validate(paged_movie)

    async def assign_pre_shuffled_list_participant(self, participant_id: uuid.UUID, subset: str):
        shuffled_lists = await self.shuffled_movie_repo.get_all_shuffled_lists_by_subset(subset)
        if shuffled_lists:
            random_list = random.choice(shuffled_lists)
            new_participant_sess = ParticipantMovieSession(participant_id, random_list.list_id)
            await self.movie_session_repo.create(new_participant_sess)
