import random
import uuid

from sqlalchemy import func

from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.repositories.study_components import StudyConditionRepository
from rssa_api.data.repositories.study_participants import StudyParticipantRepository
from rssa_api.data.schemas.participant_schemas import StudyParticipantCreate


class EnrollmentService:
    def __init__(
        self,
        participant_repo: StudyParticipantRepository,
        study_condition_repo: StudyConditionRepository,
    ):
        self.repo = participant_repo
        self.study_condition_repo = study_condition_repo

    async def enroll_participant(self, study_id: uuid.UUID, new_participant: StudyParticipantCreate) -> StudyParticipant:
        # study_conditions = await self.study_condition_repo.get_all_by_field('study_id', study_id)
        from rssa_api.data.repositories.base_repo import RepoQueryOptions
        study_conditions = await self.study_condition_repo.find_many(
            RepoQueryOptions(filters={'study_id': study_id})
        )

        if not study_conditions:
            raise ValueError(f'No study conditions found for study ID: {study_id}')
        # FIXME: make this dynamic weighted choice so that we always have n particpants for each of the k conditions
        # n%k = 0 => n_i = n_k = n/k for all i \in [1, ..., k], where n_i is the participant count in the i'th condition
        # n%k != 0 => n_i = n_k = (n-(n%k))/k & m_j = m_(k-(n%k)) = 1,
        # where n_i, and m_j are the number of participants in the i'th and j'th conditions respectively and i != j
        participant_condition = random.choice(study_conditions)

        study_participant = StudyParticipant(
            study_participant_type_id=new_participant.study_participant_type_id,
            study_id=study_id,
            study_condition_id=participant_condition.id,
            external_id=new_participant.external_id,
            current_step_id=new_participant.current_step_id,
            current_page_id=new_participant.current_page_id,
            updated_at=func.now(),
        )

        await self.repo.create(study_participant)

        return study_participant
