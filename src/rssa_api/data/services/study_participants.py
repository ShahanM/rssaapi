"""Services related to the study participants."""

import random
import string
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from async_lru import alru_cache
from fastapi import Depends
from pydantic import BaseModel
from rssa_storage.rssadb.models.participant_movie_sequence import PreShuffledMovieList, StudyParticipantMovieSession
from rssa_storage.rssadb.models.participant_responses import Feedback
from rssa_storage.rssadb.models.study_participants import (
    ParticipantStudySession,
    StudyParticipant,
)
from rssa_storage.rssadb.repositories.study_admin import PreShuffledMovieRepository
from rssa_storage.rssadb.repositories.study_components import FeedbackRepository, StudyConditionRepository
from rssa_storage.rssadb.repositories.study_participants import (
    ParticipantStudySessionRepository,
    StudyParticipantMovieSessionRepository,
    StudyParticipantRepository,
)
from rssa_storage.shared import RepoQueryOptions
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from rssa_api.data.schemas.participant_response_schemas import FeedbackBaseSchema
from rssa_api.data.schemas.participant_schemas import StudyParticipantCreate
from rssa_api.data.services.base_service import BaseService
from rssa_api.data.sources.rssadb import get_service


class EnrollmentService(BaseService[StudyParticipant, StudyParticipantRepository]):
    """Service to create and assign participant to a study condition.

    Primary Repo: StudyParticipantRepository.
    Auxiliary: StudyConditionRepository.

    """

    def __init__(
        self,
        participant_repo: StudyParticipantRepository,
        study_condition_repo: StudyConditionRepository,
    ):
        """Initialize as a participant service with access to participant type, and study conditions."""
        super().__init__(participant_repo)
        self.study_condition_repo = study_condition_repo

    async def enroll_participant(
        self, study_id: uuid.UUID, new_participant: StudyParticipantCreate
    ) -> StudyParticipant:
        """Enroll a newly created study participant to a study condition.

        Args:
            study_id: The ID of the study.
            new_participant: The new participant schema.

        Returns:
            The newly created participant.
        """
        condition_key = None
        source_meta = new_participant.source_meta
        if source_meta and new_participant.participant_type_key == 'test':
            if 'condition_key' in source_meta:
                condition_key = source_meta['condition_key']

        condition_id = await self._pick_condition(study_id, condition_key)

        study_participant = StudyParticipant(
            study_id=study_id,
            study_condition_id=condition_id,
            current_step_id=new_participant.current_step_id,
            current_page_id=new_participant.current_page_id,
            source_meta=source_meta,
            updated_at=func.now(),
        )

        await self.repo.create(study_participant)

        return study_participant

    async def _pick_condition(self, study_id: uuid.UUID, condition_key: str | None) -> uuid.UUID:
        if condition_key:
            study_condition = await self.study_condition_repo.find_one(
                RepoQueryOptions(filters={'short_code': condition_key}, load_columns=['id'])
            )
            if study_condition is None:
                raise ValueError('There was a problem with the condition key.')
            return study_condition.id

        # Ideally: Dynamic weighted choice so that we always have n participants for each of the k conditions
        # n%k = 0 => n_i = n_k = n/k for all i \in [1, ..., k], where n_i is the i'th condition's participant count
        # n%k != 0 => n_i = n_k = (n-(n%k))/k & m_j = m_(k-(n%k)) = 1,
        # where n_i, and m_j are the number of participants in the i'th and j'th conditions respectively and i != j
        # Shortcut: We remove the last assigned condition from the pool.
        condition_counts_rows = await self.study_condition_repo.get_participant_count_by_condition(
            study_id, enabled_only=True, verified_participants_only=True
        )

        if not condition_counts_rows:
            raise ValueError(f'No active study conditions found for study ID: {study_id}')

        condition_counts = {row.study_condition_id: row.participant_count for row in condition_counts_rows}
        min_count = min(condition_counts.values())
        eligible_conditions = [cond_id for cond_id, count in condition_counts.items() if count == min_count]

        return random.choice(eligible_conditions)


class PagedMoviesSchema(BaseModel):
    """A wrapper to help with navigating a list of movie ids."""

    movies: list[uuid.UUID]  # It is more accurate to say movie_ids but we are keeping this for compatibility.
    total: int


class StudyParticipantMovieSessionService(
    BaseService[StudyParticipantMovieSession, StudyParticipantMovieSessionRepository]
):
    """This service is used to maintain a randomized list of movies, which is assigned to a participant."""

    def __init__(
        self,
        movie_session_repo: StudyParticipantMovieSessionRepository,
        shuffled_movie_repo: PreShuffledMovieRepository,
    ):
        """Initialize with the PreShuffledMovieRepository as an auxiliary repo."""
        super().__init__(movie_session_repo)
        self.shuffled_movie_repo = shuffled_movie_repo

    @alru_cache(maxsize=128)
    async def get_next_session_movie_ids_batch(
        self, participant_id: uuid.UUID, offset: int, limit: int
    ) -> PagedMoviesSchema | None:
        """Fetches the next set of movies from a pre-shuffled list.

        Args:
            participant_id: The participant's id.
            offset: offset to skip
            limit: number of movies to return.

        Returns:
            A list of movies wrapped in a paging wrapper.
        """
        participant_session = await self.repo.find_one(
            options=RepoQueryOptions(
                filters={'study_participant_id': participant_id}, load_columns=['assigned_list_id']
            )
        )
        if not participant_session:
            return None

        list_id = participant_session.assigned_list_id

        pg_start = offset + 1
        pg_end = offset + limit

        # FIXME: This is a leaky abstraction. DB access belongs in the repositories
        stmt = select(
            PreShuffledMovieList.movie_ids[pg_start:pg_end], func.array_length(PreShuffledMovieList.movie_ids, 1)
        ).where(PreShuffledMovieList.id == list_id)

        result = await self.repo.db.execute(stmt)
        row = result.first()

        if not row:
            return None

        movie_ids_slice, total_count = row

        # Postgres returns None for the slice if the offset is completely out of bounds.
        # We catch that and return an empty list instead to keep the schema valid.
        if not movie_ids_slice:
            movie_ids_slice = []

        return PagedMoviesSchema(movies=movie_ids_slice, total=total_count or 0)

    async def assign_pre_shuffled_list_participant(self, participant_id: uuid.UUID, subset: str):
        """Assigned a pre-shuffled list of movies to a study_participant.

        Args:
            participant_id: The study_participant id.
            subset: A short string to identify the subset of ids to assign.
        """
        options = RepoQueryOptions(filters={'subset_desc': subset}, load_columns=['id'])
        shuffled_lists = await self.shuffled_movie_repo.find_many(options)
        if shuffled_lists:
            random_list = random.choice(shuffled_lists)
            new_participant_sess = StudyParticipantMovieSession(
                study_participant_id=participant_id, assigned_list_id=random_list.id
            )
            await self.repo.create(new_participant_sess)


class FeedbackService(BaseService[Feedback, FeedbackRepository]):
    """Service for managing participant feedback operations."""

    async def create_feedback(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, feedback_data: FeedbackBaseSchema
    ) -> Feedback:
        """Creates a new feedback entry for a participant in a study.

        Args:
            study_id: The ID of the study.
            participant_id: The ID of the participant providing feedback.
            feedback_data: The feedback data to be stored.

        Returns:
            The created Feedback object.
        """
        feedback_obj = Feedback(
            study_id=study_id,
            study_step_id=feedback_data.study_step_id,
            study_step_page_id=feedback_data.study_step_page_id,
            study_participant_id=participant_id,
            context_tag=feedback_data.context_tag,
            feedback_text=feedback_data.feedback_text,
            feedback_type=feedback_data.feedback_type,
            feedback_category=feedback_data.feedback_category,
            version=1,
        )
        feedback_item = await self.repo.create(feedback_obj)

        return feedback_item


MAX_RETRIES = 5


class ParticipantStudySessionService(BaseService[ParticipantStudySession, ParticipantStudySessionRepository]):
    """Service for managing ParticipantStudySession operations.

    Attributes:
        repo: The ParticipantStudySession repository.
    """

    async def create_session(self, participant_id: uuid.UUID) -> ParticipantStudySession | None:
        """Create a new ParticipantStudySession for the given participant."""
        for _ in range(MAX_RETRIES):
            resume_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            expires_at = datetime.now(UTC) + timedelta(hours=24)

            new_session = ParticipantStudySession(
                study_participant_id=participant_id, resume_code=resume_code, expires_at=expires_at
            )
            try:
                await self.repo.create(new_session)
                return new_session
            except IntegrityError:
                await self.repo.db.rollback()
        else:
            return None

    async def get_session_by_resume_code(self, resume_code: str) -> ParticipantStudySession | None:
        """Retrieve a ParticipantStudySession by its resume code."""
        session = await self.repo.find_one(RepoQueryOptions(filters={'resume_code': resume_code}))
        if not session:
            return None
        if session.created_at + timedelta(hours=72) < datetime.now(UTC):
            await self.repo.update(session.id, {'is_active': False})
            return None

        session_expires_at = datetime.now(UTC) + timedelta(hours=24)
        await self.repo.update(session.id, {'expires_at': session_expires_at})

        return session


EnrollmentServiceDep = Annotated[
    EnrollmentService,
    Depends(get_service(EnrollmentService, StudyParticipantRepository, StudyConditionRepository)),
]

ParticipantStudySessionServiceDep = Annotated[
    ParticipantStudySessionService,
    Depends(get_service(ParticipantStudySessionService, ParticipantStudySessionRepository)),
]
