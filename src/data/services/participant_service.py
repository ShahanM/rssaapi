import random
import uuid
from typing import List

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
	def __init__(
		self,
		participant_repo: ParticipantRepository,
		study_condition_repo: StudyConditionRepository,
		demographics_repo: DemographicsRepository,
	):
		self.participant_repo = participant_repo
		self.study_condition_repo = study_condition_repo
		self.demographics_repo = demographics_repo

	async def create_study_participant(
		self, study_id: uuid.UUID, new_participant: ParticipantCreateSchema
	) -> StudyParticipant:
		"""_summary_

		Args:
			new_participant (ParticipantCreateSchema): _description_

		Returns:
			StudyParticipant: _description_
		"""
		study_conditions = await self.study_condition_repo.get_conditions_by_study_id(study_id)

		# FIXME: make this dynamic weighted choice so that we always have n particpants for each of the k conditions
		# n%k = 0 => n_i = n_k = n/k for all i \in [1, ..., k], where n_i is the participant count in the i'th condition
		# n%k != 0 => n_i = n_k = (n-(n%k))/k & m_j = m_(k-(n%k)) = 1,
		# where n_i, and m_j are the number of participants in the i'th and j'th conditions respectively and i != j
		participant_condition = random.choice(study_conditions)

		study_participant = StudyParticipant(
			participant_type=new_participant.participant_type,
			study_id=study_id,
			condition_id=participant_condition.id,
			external_id=new_participant.external_id,
			current_step=new_participant.current_step,
			current_page=new_participant.current_page,
		)

		await self.participant_repo.create(study_participant)

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
				participant_id=demographic_data.participant_id,
				age_range=demographic_data.age_range,
				gender=demographic_data.gender,
				gender_other=demographic_data.gender_other,
				race=';'.join(demographic_data.race),
				race_other=demographic_data.race_other,
				education=demographic_data.education,
				country=demographic_data.country,
				state_region=demographic_data.state_region,
			)
			await self.demographics_repo.create(demographic_obj)

	async def get_participants_by_study_id(self, study_id: uuid.UUID) -> List[StudyParticipant]:
		"""_summary_

		Args:
			study_id (uuid.UUID): _description_

		Returns:
			List[StudyParticipant]: _description_
		"""
		return await self.participant_repo.get_all_by_field('study_id', study_id)
