from datetime import datetime
from typing import List, Union, Literal, Dict
import uuid

from pydantic import BaseModel


class ParticipantSchema(BaseModel):
	id: uuid.UUID
	study_id: uuid.UUID
	participant_type: uuid.UUID
	external_id: str
	condition_id: uuid.UUID
	current_step: uuid.UUID
	current_page: Union[uuid.UUID, None]
	date_created: datetime

	class Config:
		orm_mode = True

	def __eq__(self, other) -> bool:
		if not isinstance(other, ParticipantSchema):
			return False
		
		equalities = [self.id == other.id, self.study_id == other.study_id,\
				self.participant_type == other.participant_type,\
					self.date_created == other.date_created]

		return all(equalities)
	
	def diff(self, other):
		if self != other:
			raise Exception('Not the same participant')
		
		mismatch = []
		if self.external_id != other.external_id:
			# Technically, this should never differ if the participant is the same
			mismatch.append('external_id')
		if self.condition_id != other.condition_id:
			# Technically, this should never differ if the participant is the same
			mismatch.append('condition_id')

		if self.current_step != other.current_step:
			mismatch.append('current_step')
		if self.current_page != other.current_page:
			mismatch.append('current_page')

		return mismatch
	

class NewParticipantSchema(BaseModel):
	study_id: uuid.UUID
	participant_type: uuid.UUID
	external_id: str
	current_step: uuid.UUID
	current_page: Union[uuid.UUID, None]


class SurveyItemResponse(BaseModel):
	item_id: Union[uuid.UUID, None]
	response: str


class SurveyResponse(BaseModel):
	participant_id: uuid.UUID
	page_id: uuid.UUID

	responses: List[SurveyItemResponse]


class TextResponse(BaseModel):
	construct_id: uuid.UUID
	item_id: uuid.UUID
	response: str


class GroupedTextResponse(BaseModel):
	participant_id: uuid.UUID
	page_id: uuid.UUID
	responses: List[TextResponse]


class DemographicSchema(BaseModel):
	age_range: str
	gender: str
	gender_other: str
	race: List[str]
	race_other: str
	education: str
	country: str
	state_region: str


class FeedbackSchema(BaseModel):
	participant_id: uuid.UUID
	feedback: str
	feedback_type: str
	feedback_category: str