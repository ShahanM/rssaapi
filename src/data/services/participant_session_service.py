import random
import uuid
from typing import List

from data.models.participant_movie_sequence import ParticipantMovieSession
from data.repositories.participant_movie_session import ParticipantMovieSessionRepository
from data.repositories.pre_shuffled_movie_list import PreShuffledMovieRepository


class ParticipantSessionService:
	def __init__(
		self,
		movie_session_repo: ParticipantMovieSessionRepository,
		shuffled_movie_repo: PreShuffledMovieRepository,
	):
		self.movie_session_repo = movie_session_repo
		self.shuffled_movie_repo = shuffled_movie_repo

	async def get_next_session_movie_ids_batch(
		self, participant_id: uuid.UUID, offset: int, limit: int
	) -> List[uuid.UUID]:
		participant_assigned_list = await self.movie_session_repo.get_movie_session_by_participant_id(participant_id)
		movie_ids = list(participant_assigned_list.assigned_list.movie_ids)
		return movie_ids[offset : min(offset + limit, len(movie_ids))]

	async def assign_pre_shuffled_list_participant(self, participant_id: uuid.UUID, subset: str):
		shuffled_lists = await self.shuffled_movie_repo.get_all_shuffled_lists_by_subset(subset)
		if shuffled_lists:
			random_list = random.choice(shuffled_lists)
			new_participant_sess = ParticipantMovieSession(participant_id, random_list.list_id)
			await self.movie_session_repo.create(new_participant_sess)
