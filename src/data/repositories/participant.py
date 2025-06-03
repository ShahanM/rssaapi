import random
import uuid
from typing import List, Union

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from data.models.schemas.participantschema import DemographicSchema
from data.models.study_components import (
	Page,
	Step,
)
from data.models.study_participants import (
	ParticipantType,
	StudyParticipant,
)
from data.repositories.base_repo import BaseRepository


class ParticipantRepository(BaseRepository[StudyParticipant]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, StudyParticipant)

	# async def create_study_participant(
	# 	self,
	# 	study_id: uuid.UUID,
	# 	participant_type: uuid.UUID,
	# 	external_id: str,
	# 	current_step: uuid.UUID,
	# 	current_page: Union[uuid.UUID, None] = None,
	# ) -> ParticipantSchema:
	# 	study_participant = StudyParticipant(
	# 		participant_type=participant_type,
	# 		study_id=study_id,
	# 		condition_id=condition_id,
	# 		external_id=external_id,
	# 		current_step=current_step,
	# 		current_page=current_page
	# 	)

	# 	if not study_conditions:
	# 		raise HTTPException(status_code=404, detail='No study conditions found for study: ' + str(self.study.id))

	# 	condition = random.choice(study_conditions)

	# 	step_repo = StudyStepRepository(self.db)
	# 	cstep = await step_repo.get_study_step_by_id(current_step)
	# 	# cstep = self.db.query(Step).where(Step.id == current_step).first()
	# 	cpage = None

	# 	if current_page is not None:
	# 		cpage = self.db.query(Page).where(Page.id == current_page).first()

	# 	ptype = get_participant_type_by_id(self.db, participant_type)
	# 	participant = StudyParticipant(
	# 		participant_type=ptype.id,
	# 		study_id=self.study.id,
	# 		condition_id=condition.id,
	# 		current_step=cstep.id,
	# 		external_id=external_id,
	# 		current_page=cpage.id if cpage is not None else None,
	# 	)

	# 	self.db.add(participant)
	# 	self.db.commit()
	# 	self.db.refresh(participant)

	# 	return ParticipantSchema.model_validate(participant)

	# def get_study_participants(self, study_id: uuid.UUID) -> List[ParticipantSchema]:
	# 	participants = self.db.query(StudyParticipant).filter(StudyParticipant.study_id == self.study.id).all()

	# 	if not participants:
	# 		return []
	# 	return [ParticipantSchema.model_validate(participant) for participant in participants]

	# def get_study_participant_by_id(self, participant_id: uuid.UUID) -> ParticipantSchema:
	# 	participant = self.db.query(StudyParticipant).where(StudyParticipant.id == participant_id).first()
	# 	if not participant:
	# 		raise HTTPException(status_code=404, detail='Participant not found')

	# 	return ParticipantSchema.model_validate(participant)


"""
The following functions are going to be refactored into the ParticipantRepository class
"""


def get_participant_types(db: Session) -> List[ParticipantType]:
	types = db.query(ParticipantType).all()

	return types


def get_participant_type_by_id(db: Session, type_id: uuid.UUID) -> ParticipantType:
	ptype = db.query(ParticipantType).where(ParticipantType.id == type_id).first()
	if not ptype:
		raise HTTPException(status_code=404, detail='Participant type not found')

	return ptype


def create_participant_type(db: Session, type: str) -> ParticipantType:
	participant_type = ParticipantType(type=type)
	db.add(participant_type)
	db.commit()
	db.refresh(participant_type)

	return participant_type


# implemented but not tested
def get_study_participants(db: Session, study_id: uuid.UUID) -> List[StudyParticipant]:
	participants = db.query(StudyParticipant).where(StudyParticipant.study_id == study_id).all()

	return participants


# implemented but not tested
def get_study_participant_by_id(db: Session, participant_id: uuid.UUID) -> StudyParticipant:
	participant = db.query(StudyParticipant).where(StudyParticipant.id == participant_id).first()
	if not participant:
		raise HTTPException(status_code=404, detail='Participant not found')

	return participant


def create_study_participant(
	db: Session,
	study_id: uuid.UUID,
	participant_type: uuid.UUID,
	external_id: str,
	current_step: uuid.UUID,
	current_page: Union[uuid.UUID, None] = None,
) -> StudyParticipant:
	study = get_study_by_id(db, study_id)
	study_conditions = get_study_conditions(db, study_id)

	if not study_conditions:
		raise HTTPException(status_code=404, detail='No study conditions found for study: ' + str(study.id))

	condition = random.choice(study_conditions)

	cstep = db.query(Step).where(Step.id == current_step).first()
	cpage = None
	if current_page is not None:
		cpage = db.query(Page).where(Page.id == current_page).first()
	ptype = get_participant_type_by_id(db, participant_type)
	participant = StudyParticipant(
		participant_type=ptype.id,
		study_id=study.id,
		condition_id=condition.id,
		current_step=cstep.id,
		external_id=external_id,
		current_page=cpage.id if cpage is not None else None,
	)
	db.add(participant)
	db.commit()
	db.refresh(participant)

	return participant


# def create_participant_response(db: Session, participant_id: UUID, construct_id: UUID,
# 		response: str, item_id: Union[UUID, None] = None) -> ParticipantResponse:
# 	partres = ParticipantResponse(participant_id=participant_id, construct_id=construct_id,
# 			response=response, item_id=item_id)
# 	db.add(response)
# 	db.commit()
# 	db.refresh(response)

# 	return partres


def create_participant_demographic(db: Session, participant_id: uuid.UUID, demographic: DemographicSchema) -> bool:
	participant = get_study_participant_by_id(db, participant_id)
	if not participant:
		raise HTTPException(status_code=404, detail='Participant not found')

	def none_if_empty(value: str) -> Union[str, None]:
		return value if len(value) > 0 else None

	demog = Demographic(
		participant_id=participant.id,
		age_range=demographic.age_range,
		gender=demographic.gender,
		gender_other=none_if_empty(demographic.gender_other),
		race=';'.join(demographic.race),
		race_other=none_if_empty(demographic.race_other),
		education=demographic.education,
		country=demographic.country,
		state_region=none_if_empty(demographic.state_region),
	)

	db.add(demog)
	db.commit()
	db.refresh(demog)

	return True


def create_feedback(
	db: Session, participant_id: uuid.UUID, feedback: str, feedback_type: str, feedback_category: str
) -> bool:
	participant = get_study_participant_by_id(db, participant_id)
	if not participant:
		raise HTTPException(status_code=404, detail='Participant not found')

	feedbackobj = Feedback(
		participant_id=participant.id,
		study_id=participant.study_id,
		feedback=feedback,
		feedback_type=feedback_type,
		feedback_category=feedback_category,
	)

	db.add(feedbackobj)
	db.commit()
	db.refresh(feedbackobj)

	return True
