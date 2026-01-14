import random
import string
import uuid
from datetime import UTC, datetime, timedelta

from async_lru import alru_cache
from pydantic import BaseModel
from rssa_storage.rssadb.models.participant_movie_sequence import StudyParticipantMovieSession
from rssa_storage.rssadb.models.participant_responses import Feedback
from rssa_storage.rssadb.models.study_participants import ParticipantStudySession, StudyParticipant
from rssa_storage.rssadb.repositories.study_admin import PreShuffledMovieRepository
from rssa_storage.rssadb.repositories.study_components import FeedbackRepository, StudyConditionRepository
from rssa_storage.rssadb.repositories.study_participants import (
    ParticipantStudySessionRepository,
    StudyParticipantMovieSessionRepository,
    StudyParticipantRepository,
    StudyParticipantTypeRepository,
)
from rssa_storage.shared import RepoQueryOptions
from sqlalchemy import func
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
        super().__init__(participant_repo)
        self.participant_type_repo = participant_type_repo
        self.study_condition_repo = study_condition_repo

    async def enroll_participant(
        self, study_id: uuid.UUID, new_participant: StudyParticipantCreate
    ) -> StudyParticipant:
        study_conditions = await self.study_condition_repo.find_many(RepoQueryOptions(filters={'study_id': study_id, 'enabled': True}))

        if not study_conditions:
            raise ValueError(f'No study conditions found for study ID: {study_id}')
        # FIXME: make this dynamic weighted choice so that we always have n participants for each of the k conditions
        # n%k = 0 => n_i = n_k = n/k for all i \in [1, ..., k], where n_i is the participant count in the i'th condition
        # n%k != 0 => n_i = n_k = (n-(n%k))/k & m_j = m_(k-(n%k)) = 1,
        # where n_i, and m_j are the number of participants in the i'th and j'th conditions respectively and i != j
        participant_condition = random.choice(study_conditions)

        participant_type = await self.participant_type_repo.find_one(RepoQueryOptions(filters={'type': new_participant.participant_type_key}))
        if not participant_type:
            participant_type = await self.participant_type_repo.find_one(RepoQueryOptions(filters={'type': 'unknown'}))
                
        study_participant = StudyParticipant(
            study_participant_type_id=participant_type.id,
            study_id=study_id,
            study_condition_id=participant_condition.id,
            external_id=new_participant.external_id,
            current_step_id=new_participant.current_step_id,
            current_page_id=new_participant.current_page_id,
            updated_at=func.now(),
        )

        await self.repo.create(study_participant)

        return study_participant


class PagedMoviesSchema(BaseModel):
    movies: list[uuid.UUID]
    total: int


class StudyParticipantMovieSessionService(
    BaseService[StudyParticipantMovieSession, StudyParticipantMovieSessionRepository]
):
    def __init__(
        self,
        movie_session_repo: StudyParticipantMovieSessionRepository,
        shuffled_movie_repo: PreShuffledMovieRepository,
    ):
        super().__init__(movie_session_repo)
        self.shuffled_movie_repo = shuffled_movie_repo

    @alru_cache(maxsize=128)
    async def get_next_session_movie_ids_batch(
        self, participant_id: uuid.UUID, offset: int, limit: int
    ) -> PagedMoviesSchema | None:
        participant_assigned_list = await self.repo.get_movie_session_by_participant_id(participant_id)
        if not participant_assigned_list:
            return None
        movie_ids = list(participant_assigned_list.assigned_list.movie_ids)

        paged_movie = {'movies': movie_ids[offset : min(offset + limit, len(movie_ids))], 'total': len(movie_ids)}

        return PagedMoviesSchema.model_validate(paged_movie)

    async def assign_pre_shuffled_list_participant(self, participant_id: uuid.UUID, subset: str):
        shuffled_lists = await self.shuffled_movie_repo.get_all_shuffled_lists_by_subset(subset)
        if shuffled_lists:
            random_list = random.choice(shuffled_lists)
            new_participant_sess = StudyParticipantMovieSession(
                study_participant_id=participant_id, assigned_list_id=random_list.id
            )
            await self.repo.create(new_participant_sess)


"""Service layer for handling participant feedback operations."""


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
        # session = await self.repo.get_by_field('resume_code', resume_code)
        session = await self.repo.find_one(RepoQueryOptions(filters={'resume_code': resume_code}))
        if not session:
            return None
        if session.created_at + timedelta(hours=72) < datetime.now(UTC):
            await self.repo.update(session.id, {'is_active': False})
            return None

        session_expires_at = datetime.now(UTC) + timedelta(hours=24)
        await self.repo.update(session.id, {'expires_at': session_expires_at})

        return session
