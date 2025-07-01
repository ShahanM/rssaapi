import random
import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_participants import Demographic, StudyParticipant
from data.repositories.demographics import DemographicsRepository
from data.repositories.participant import ParticipantRepository
from data.repositories.study_condition import StudyConditionRepository
from data.schemas.participant_schemas import (
	DemographicsCreateSchema,
	ParticipantCreateSchema,
	ParticipantSchema,
	ParticipantUpdateSchema,
)


class ParticipantService:
	def __init__(self, db: AsyncSession):
		self.db = db
		self.participant_repo = ParticipantRepository(db)
		self.study_condition_repo = StudyConditionRepository(db)
		self.demographics_repo = DemographicsRepository(db)

	async def create_study_participant(self, new_participant: ParticipantCreateSchema) -> StudyParticipant:
		"""_summary_

		Args:
			new_participant (ParticipantCreateSchema): _description_

		Returns:
			StudyParticipant: _description_
		"""
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

		await self.db.refresh(study_participant)

		return study_participant

	async def update_study_participant(self, new_participant_data: ParticipantUpdateSchema) -> ParticipantSchema:
		"""_summary_

		Args:
			new_participant_data (ParticipantUpdateSchema): _description_

		Returns:
			ParticipantSchema: _description_
		"""
		update_dict = new_participant_data.model_dump()
		updated_participant = await self.participant_repo.update(new_participant_data.id, update_dict)

		await self.db.refresh(updated_participant)
		await self.db.commit()

		return ParticipantSchema.model_validate(updated_participant)

	async def create_or_update_demographic_info(self, demographic_data: DemographicsCreateSchema):
		"""_summary_

		Args:
			demographic_data (DemographicsCreateSchema): _description_
		"""
		demographic_obj = await self.demographics_repo.get_by_field('participant_id', demographic_data.participant_id)
		if demographic_obj:
			update_dict = demographic_data.model_dump()

			await self.demographics_repo.update(demographic_obj.id, update_dict)
		else:
			demographic_obj = Demographic(
				demographic_data.participant_id,
				demographic_data.age_range,
				demographic_data.gender,
				';'.join(demographic_data.race),
				demographic_data.education,
				demographic_data.country,
				demographic_data.state_region,
				demographic_data.gender_other,
				demographic_data.race_other,
			)
			await self.demographics_repo.create(demographic_obj)

		await self.db.refresh(demographic_obj)
		await self.db.commit()

	async def get_participants_by_study_id(self, study_id: uuid.UUID) -> List[StudyParticipant]:
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_

		Returns:
			List[StudyParticipant]: _description_
		"""
		return await self.participant_repo.get_all_by_field('study_id', study_id)
