from datetime import datetime
from typing import List, Union, Literal
import uuid

from pydantic import BaseModel


# class QuestionSchema(BaseModel):
# 	id: Union[int, None]
# 	page_id: Union[int, None]
# 	question_order: Union[int, None]
# 	question: Union[str, None]

# 	class Config:
# 		orm_mode = True


# class NewQuestionSchema(BaseModel):
# 	question_order: int
# 	questiontxt: str


# class PageSchema(BaseModel):
# 	id: Union[int, None]
# 	step_id: Union[int, None]
# 	page_order: Union[int, None]
# 	page_name: Union[str, None]
# 	page_instruction: Union[str, None]

# 	questions: List[QuestionSchema]

# 	class Config:
# 		orm_mode = True


# class NewPageSchema(BaseModel):
# 	page_order: int
# 	page_name: str
# 	page_instruction: str


# class StepSchema(BaseModel):
# 	id: Union[int, None]
# 	study_id: Union[int, None]
# 	step_order: Union[int, None]
# 	step_name: Union[str, None]
# 	step_description: Union[str, None]

# 	# pages: List[PageSchema]

# 	class Config:
# 		orm_mode = True


# class NewStepSchema(BaseModel):
# 	step_order: int
# 	step_name: str
# 	step_description: str


# class StudyConditionSchema(BaseModel):
# 	id: int
# 	study_id: int
# 	condition_name: str

# 	class Config:
# 		orm_mode = True


# class StudySchema(BaseModel):
# 	id: int
# 	date_created: datetime
# 	study_name: str

# 	# steps: List[StepSchema]
# 	conditions: List[StudyConditionSchema]

# 	class Config:
# 		orm_mode = True


# class NewConditionSchema(BaseModel):
# 	condition_name: str

# New schemas for API v2
class CreateMetaModel(BaseModel):
	name: str
	description: str


class MetaModel(CreateMetaModel):
	id: uuid.UUID
	date_created: datetime

	class Config:
		orm_mode = True


class OrderedCreateMetaModel(CreateMetaModel):
	order_position: int


class OrderedMetaModel(MetaModel):
	order_position: int

	class Config:
		orm_mode = True


class CreateStudySchema(CreateMetaModel):
	pass


class CreateStudyConditionSchema(CreateMetaModel):
	study_id: uuid.UUID


class StudyConditionSchema(MetaModel):
	study_id: uuid.UUID

	class Config:
		orm_mode = True


class StudyAuthSchema(MetaModel):
	pass


class StudySchema(MetaModel):
	conditions: List[StudyConditionSchema]

	class Config:
		orm_mode = True


class CreateStepSchema(OrderedCreateMetaModel):
	study_id: uuid.UUID


class StepPageSchema(OrderedMetaModel):
	study_id: uuid.UUID
	step_id: uuid.UUID


class StudyStepSchema(OrderedMetaModel):
	study_id: uuid.UUID
	pages: List[StepPageSchema]


class CreatePageSchema(OrderedCreateMetaModel):
	study_id: uuid.UUID
	step_id: uuid.UUID


class Auth0UserSchema(BaseModel):
	iss: str
	sub: str
	aud: List[str]
	iat: int
	exp: int
	scope: str
	azp: str
	permissions: List[str]


class ConstructItemSchema(BaseModel):
	id: uuid.UUID
	construct_id: uuid.UUID
	text: str
	order_position: int
	item_type: uuid.UUID

	class Config:
		orm_mode = True


class CreateConstructItemSchema(BaseModel):
	construct_id: uuid.UUID
	item_type: uuid.UUID
	text: str
	order_position: int



class SurveyConstructSchema(BaseModel):
	id: uuid.UUID
	name: str
	desc: str
	# TODO: Add the name field for construct type and scale
	class Config:
		orm_mode = True



class ConstructTypeSchema(BaseModel):
	id: uuid.UUID
	type: str

	class Config:
		orm_mode = True


class ConstructScaleSchema(BaseModel):
	id: uuid.UUID
	levels: int
	name: str

	class Config:
		orm_mode = True

class ScaleLevelSchema(BaseModel):
	level: int
	label: str
	scale_id: uuid.UUID

	class Config:
		orm_mode = True


class ConstructScaleDetailSchema(ConstructScaleSchema):
	scale_levels: List[ScaleLevelSchema]

	class Config:
		orm_mode = True


class SurveyConstructDetailSchema(BaseModel):
	id: uuid.UUID
	name: str
	desc: str
	type: Union[ConstructTypeSchema, None]
	scale: Union[ConstructScaleDetailSchema, None]
	items: List[ConstructItemSchema]

	class Config:
		orm_mode = True


class NewSurveyConstructSchema(BaseModel):
	name: str
	desc: str
	type_id: uuid.UUID
	scale_id: uuid.UUID


class ConstructItemTypeSchema(BaseModel):
	id: uuid.UUID
	type: str

	class Config:
		orm_mode = True


class NewConstructItemTypeSchema(BaseModel):
	type: str


class NewConstructTypeSchema(BaseModel):
	type: str


class NewScaleLevelSchema(BaseModel):
	level: int
	label: str


class NewConstructScaleSchema(BaseModel):
	levels: int
	name: str
	scale_levels: List[NewScaleLevelSchema]


class UpdateSurveyConstructSchema(BaseModel):
	id: uuid.UUID
	name: Union[str, None] = None
	desc: Union[str, None] = None
	construct_type: Union[uuid.UUID, None] = None
	construct_scale: Union[uuid.UUID, None] = None


class CreatePageContentSchema(BaseModel):
	page_id: uuid.UUID
	construct_id: uuid.UUID
	order_position: int


class SurveyPageSchema(BaseModel):
	step_id: uuid.UUID
	page_id: uuid.UUID
	order_position: int
	construct_id: uuid.UUID
	construct_items: List[ConstructItemSchema]
	construct_scale: List[ScaleLevelSchema]


class ParticipantTypeSchema(BaseModel):
	id: str
	type: str

	class Config:
		orm_mode = True


class NewParticipantTypeSchema(BaseModel):
	type: str


class StepIdRequestSchema(BaseModel):
	current_step_id: uuid.UUID



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


# {
# 	'iss': 'https://dev-ezaapkd1uq45qy8u.us.auth0.com/', 
# 	'sub': 'auth0|667f78dc16bf3a06dc53f472', 
# 	'aud': ['https://rssa.recsys.dev/api/', 'https://dev-ezaapkd1uq45qy8u.us.auth0.com/userinfo'], 
# 	'iat': 1721768272, 'exp': 1721854672, 
# 	'scope': 'openid profile email', 
# 	'azp': 'L1eKFXJ57zarQhNkGTEB0YfPHCokSQNI', 
# 	'permissions': ['delete:all', 'read:all', 'write:all']
# 	}