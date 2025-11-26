import random
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from async_lru import alru_cache
from sqlalchemy import func

from rssa_api.data.models.study_participants import Demographic, ParticipantRecommendationContext, StudyParticipant
from rssa_api.data.repositories.study_components import StudyConditionRepository
from rssa_api.data.repositories.study_participants import (
    ParticipantDemographicRepository,
    ParticipantRecommendationContextRepository,
    StudyParticipantRepository,
)
from rssa_api.data.schemas.base_schemas import UpdatePayloadSchema
from rssa_api.data.schemas.participant_schemas import (
    DemographicsBaseSchema,
    DemographicsSchema,
    ParticipantSchema,
    ParticpantBaseSchema,
)
from rssa_api.data.schemas.preferences_schemas import RecommendationContextBaseSchema, RecommendationContextSchema
from rssa_api.data.utility import convert_datetime_to_str, convert_uuids_to_str


class StudyParticipantService:
    def __init__(
        self,
        participant_repo: StudyParticipantRepository,
        study_condition_repo: StudyConditionRepository,
        demographics_repo: ParticipantDemographicRepository,
        recommendation_context_repo: ParticipantRecommendationContextRepository,
    ):
        self.repo = participant_repo
        self.study_condition_repo = study_condition_repo
        self.demographics_repo = demographics_repo
        self.recommendation_context_repo = recommendation_context_repo

    async def create_study_participant(
        self, study_id: uuid.UUID, new_participant: ParticpantBaseSchema
    ) -> StudyParticipant:
        study_conditions = await self.study_condition_repo.get_conditions_by_study_id(study_id)

        # FIXME: make this dynamic weighted choice so that we always have n particpants for each of the k conditions
        # n%k = 0 => n_i = n_k = n/k for all i \in [1, ..., k], where n_i is the participant count in the i'th condition
        # n%k != 0 => n_i = n_k = (n-(n%k))/k & m_j = m_(k-(n%k)) = 1,
        # where n_i, and m_j are the number of participants in the i'th and j'th conditions respectively and i != j
        participant_condition = random.choice(study_conditions)

        study_participant = StudyParticipant(
            participant_type_id=new_participant.participant_type_id,
            study_id=study_id,
            condition_id=participant_condition.id,
            external_id=new_participant.external_id,
            current_step_id=new_participant.current_step_id,
            current_page_id=new_participant.current_page_id,
            updated_at=func.now(),
        )

        await self.repo.create(study_participant)

        return study_participant

    async def update_study_participant(
        self, participant_id: uuid.UUID, update_data: UpdatePayloadSchema
    ) -> ParticipantSchema:
        updated_participant = await self.repo.update(participant_id, update_data.updated_fields)

        return ParticipantSchema.model_validate(updated_participant)

    async def create_demographic_info(
        self, participant_id: uuid.UUID, demographic_data: DemographicsBaseSchema
    ) -> DemographicsSchema:
        demographic_obj = Demographic(
            participant_id=participant_id,
            age_range=demographic_data.age_range,
            gender=demographic_data.gender,
            gender_other=demographic_data.gender_other,
            race=';'.join(demographic_data.race),
            race_other=demographic_data.race_other,
            education=demographic_data.education,
            country=demographic_data.country,
            state_region=demographic_data.state_region,
            updated_at=datetime.now(timezone.utc),
            version=1,
        )
        await self.demographics_repo.create(demographic_obj)

        return DemographicsSchema.model_validate(demographic_obj)

    async def update_demographic_info(
        self, demographics_id: uuid.UUID, update_data: dict[str, Any], client_version: int
    ) -> int:
        return await self.demographics_repo.update_response(demographics_id, update_data, client_version)

    async def get_participants_by_study_id(self, study_id: uuid.UUID) -> List[StudyParticipant]:
        return await self.repo.get_all_by_field('study_id', study_id)

    async def get_participant(self, participant_id: uuid.UUID) -> Optional[ParticipantSchema]:
        participant = await self.repo.get(participant_id)
        if not participant:
            return None
        return ParticipantSchema.model_validate(participant)

    async def create_recommendation_context(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, context_data: RecommendationContextBaseSchema
    ) -> RecommendationContextSchema:
        raw_dict = context_data.recommendations_json.model_dump()
        json_safe_dict = convert_uuids_to_str(raw_dict)
        json_safe_dict = convert_datetime_to_str(json_safe_dict)
        rec_ctx = ParticipantRecommendationContext(
            study_id=study_id,
            step_id=context_data.step_id,
            step_page_id=context_data.step_page_id,
            participant_id=participant_id,
            context_tag=context_data.context_tag,
            recommendations_json=json_safe_dict,
        )
        await self.recommendation_context_repo.create(rec_ctx)

        return RecommendationContextSchema.model_validate(rec_ctx)

    @alru_cache(maxsize=128)
    async def get_recommndation_context_by_participant_context(
        self, study_id: uuid.UUID, participant_id: uuid.UUID, context_tag: str
    ) -> Optional[RecommendationContextSchema]:
        rec_ctx = await self.recommendation_context_repo.get_by_fields(
            [('study_id', study_id), ('participant_id', participant_id), ('context_tag', context_tag)]
        )

        if not rec_ctx:
            return None

        return RecommendationContextSchema.model_validate(rec_ctx)
