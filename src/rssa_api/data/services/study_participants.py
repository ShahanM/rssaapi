"""Services related to the study participants."""

import random
import string
import uuid
from datetime import UTC, datetime, timedelta

from async_lru import alru_cache
from pydantic import BaseModel
from rssa_storage.rssadb.models.participant_movie_sequence import ShuffledMovieListItem, StudyParticipantMovieSession
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
    StudyParticipantTypeRepository,
)
from rssa_storage.shared import RepoQueryOptions
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from rssa_api.data.schemas.participant_response_schemas import FeedbackBaseSchema
from rssa_api.data.schemas.participant_schemas import StudyParticipantCreate
from rssa_api.data.services.base_service import BaseService


class EnrollmentService(BaseService[StudyParticipant, StudyParticipantRepository]):
    """Service to create and assign participant to a study condition.

    Primary Repo: StudyParticipantRepository.
    Auxiliary: StudyConditionRepository.

    """

    def __init__(
        self,
        participant_repo: StudyParticipantRepository,
        participant_type_repo: StudyParticipantTypeRepository,
        study_condition_repo: StudyConditionRepository,
    ):
        """Initialize as a participant service with access to participant type, and study conditions."""
        super().__init__(participant_repo)
        self.participant_type_repo = participant_type_repo
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
        participant_type = await self.participant_type_repo.find_one(
            RepoQueryOptions(filter_ilike={'type': new_participant.participant_type_key})
        )
        if not participant_type:
            participant_type = await self.participant_type_repo.find_one(RepoQueryOptions(filters={'type': 'unknown'}))

        if not participant_type:
            raise ValueError('No default participant_type in the database. Please get in touch with an adult.')

        condition_key = None
        if participant_type.type == 'test':
            if 'condition_key' in new_participant.source_meta:
                condition_key = new_participant.source_meta['condition_key']

        condition_id = await self._pick_condition(study_id, condition_key)

        study_participant = StudyParticipant(
            study_participant_type_id=participant_type.id,
            study_id=study_id,
            study_condition_id=condition_id,
            external_id=new_participant.external_id,
            current_step_id=new_participant.current_step_id,
            current_page_id=new_participant.current_page_id,
            source_meta=new_participant.source_meta,
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

        condition_pool = await self.study_condition_repo.find_many(
            RepoQueryOptions(filters={'study_id': study_id, 'enabled': True}, load_columns=['id'])
        )

        if not condition_pool:
            raise ValueError(f'No study conditions found for study ID: {study_id}')

        # Ideally: Dynamic weighted choice so that we always have n participants for each of the k conditions
        # n%k = 0 => n_i = n_k = n/k for all i \in [1, ..., k], where n_i is the i'th condition's participant count
        # n%k != 0 => n_i = n_k = (n-(n%k))/k & m_j = m_(k-(n%k)) = 1,
        # where n_i, and m_j are the number of participants in the i'th and j'th conditions respectively and i != j
        # Shortcut: We remove the last assigned condition from the pool.
        last_participant = await self.repo.find_one(
            RepoQueryOptions(
                filters={'study_id': study_id, 'discarded': False},
                sort_by='created_at',
                sort_desc=True,
                load_columns=['id', 'study_condition_id'],
            )
        )
        if last_participant:
            if len(condition_pool) > 1:
                condition_pool = [cond for cond in condition_pool if not cond.id == last_participant.study_condition_id]
        study_condition = random.choice(condition_pool)

        return study_condition.id


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
        """Fetches the next set of movies from a pre shuffles list.

        Args:
            participant_id: The participant's id.
            offset: offset to skip
            limit: number of movies to return.

        Returns:
            A list of movies wrapped in a paging wrapper.
        """
        participant_session = await self.repo.get_movie_session_by_participant_id(participant_id)
        if not participant_session:
            return None

        list_id = participant_session.assigned_list_id

        stmt = (
            select(ShuffledMovieListItem.movie_id)
            .where(ShuffledMovieListItem.shuffle_list_id == list_id)
            .order_by(ShuffledMovieListItem.position.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.repo.db.execute(stmt)
        movie_ids = list(result.scalars().all())

        if not movie_ids:
            return None

        count_stmt = select(func.count()).where(ShuffledMovieListItem.shuffle_list_id == list_id)
        total_count = await self.repo.db.scalar(count_stmt)

        return PagedMoviesSchema(movies=movie_ids, total=total_count or 0)

    async def assign_pre_shuffled_list_participant(self, participant_id: uuid.UUID, subset: str):
        """Assigned a pre-shuffled list of movies to a study_participant.

        Args:
            participant_id: The study_participant id.
            subset: A short string to identify the subset of ids to assign.
        """
        shuffled_lists = await self.shuffled_movie_repo.get_all_shuffled_lists_by_subset(subset)
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
        """Create a new ParticipantStudySession for the given participant.

        Args:
            participant_id: The ID of the participant.

        Returns:
            The created ParticipantStudySession, or None if creation failed after retries.
        """
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
        """Retrieve a ParticipantStudySession by its resume code.

        Args:
            resume_code: The resume code of the session.

        Returns:
            The ParticipantStudySession if found and valid, else None.
        """
        session = await self.repo.find_one(RepoQueryOptions(filters={'resume_code': resume_code}))
        if not session:
            return None
        if session.created_at + timedelta(hours=72) < datetime.now(UTC):
            await self.repo.update(session.id, {'is_active': False})
            return None

        session_expires_at = datetime.now(UTC) + timedelta(hours=24)
        await self.repo.update(session.id, {'expires_at': session_expires_at})

        return session
