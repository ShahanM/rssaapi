import random

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.participant import StudyParticipant
from data.repositories.participant import ParticipantRepository
from data.repositories.study_condition import StudyConditionRepository
from data.schemas.participant_schemas import ParticipantCreateSchema, ParticipantSchema, ParticipantUpdateSchema


class ParticipantService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.participant_repo = ParticipantRepository(db)
		self.study_condition_repo = StudyConditionRepository(db)

	async def create_study_participant(self, new_participant: ParticipantCreateSchema) -> ParticipantSchema:
		study_conditions = await self.study_condition_repo.get_conditions_by_study_id(new_participant.study_id)

		# FIXME: make this dynamic weighted choice so that we always have n particpants for each of the k conditions
		# n%k = 0 => n_i = n_k = n/k for all i \in [1, ..., k], where n_i is the participant count in the i'th condition
		# n%k != 0 => n_i = n_k = (n-(n%k))/k & m_j = m_(k-(n%k)) = 1,
		# where n_i, and m_j are the number of participants in the i'th and j'th conditions respectively and i != j
		participant_condition = random.choice(study_conditions)

		study_participant = StudyParticipant(
			participant_type=new_participant.participant_type,
			study_id=new_participant.study_id,
			condition_id=participant_condition.id,
			external_id=new_participant.external_id,
			current_step=new_participant.current_step,
			current_page=new_participant.current_page,
		)

		await self.participant_repo.create(study_participant)

		await self.db.commit()
		await self.db.refresh(study_participant)

		return ParticipantSchema.model_validate(study_participant)

	async def update_study_participant(self, new_participant_data: ParticipantUpdateSchema) -> ParticipantSchema:
		update_dict = new_participant_data.model_dump()
		updated_participant = await self.participant_repo.update(new_participant_data.id, update_dict)

		await self.db.commit()
		await self.db.refresh(updated_participant)

		return ParticipantSchema.model_validate(updated_participant)
