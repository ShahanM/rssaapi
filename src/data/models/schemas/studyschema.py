import uuid
from datetime import datetime
from typing import List, Union

from pydantic import BaseModel, ConfigDict


# New schemas for API v2
class CreateMetaModel(BaseModel):
	name: str
	description: str


class MetaModel(CreateMetaModel):
	id: uuid.UUID
	date_created: datetime

	model_config = ConfigDict(from_attributes=True)


class OrderedCreateMetaModel(CreateMetaModel):
	order_position: int


class OrderedMetaModel(MetaModel):
	order_position: int

	model_config = ConfigDict(from_attributes=True)


class CreateStudySchema(CreateMetaModel):
	pass


class CreateStudyConditionSchema(CreateMetaModel):
	study_id: uuid.UUID


class StudyConditionSchema(MetaModel):
	study_id: uuid.UUID

	model_config = ConfigDict(from_attributes=True)


class StudyAuthSchema(MetaModel):
	pass


class StudySchema(MetaModel):
	conditions: List[StudyConditionSchema]

	model_config = ConfigDict(from_attributes=True)


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

	model_config = ConfigDict(from_attributes=True)


class CreateConstructItemSchema(BaseModel):
	construct_id: uuid.UUID
	item_type: uuid.UUID
	text: str
	order_position: int


class ConstructTypeSchema(BaseModel):
	id: uuid.UUID
	type: str

	model_config = ConfigDict(from_attributes=True)


class ConstructScaleSchema(BaseModel):
	id: uuid.UUID
	levels: int
	name: str

	model_config = ConfigDict(from_attributes=True)


class SurveyConstructSchema(BaseModel):
	id: uuid.UUID
	name: str
	desc: str
	type: ConstructTypeSchema
	scale: Union[uuid.UUID, None]

	model_config = ConfigDict(from_attributes=True)


class ScaleLevelSchema(BaseModel):
	level: int
	label: str
	scale_id: uuid.UUID

	model_config = ConfigDict(from_attributes=True)


class ConstructScaleDetailSchema(ConstructScaleSchema):
	scale_levels: List[ScaleLevelSchema]

	model_config = ConfigDict(from_attributes=True)


class SurveyConstructDetailSchema(BaseModel):
	id: uuid.UUID
	name: str
	desc: str
	type: Union[ConstructTypeSchema, None]
	scale: Union[ConstructScaleDetailSchema, None]
	items: List[ConstructItemSchema]

	model_config = ConfigDict(from_attributes=True)


class NewSurveyConstructSchema(BaseModel):
	name: str
	desc: str
	type_id: uuid.UUID
	scale_id: str


class ConstructItemTypeSchema(BaseModel):
	id: uuid.UUID
	type: str

	model_config = ConfigDict(from_attributes=True)


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


class PageContentSchema(BaseModel):
	page_id: uuid.UUID
	construct_id: uuid.UUID
	order_position: int
	construct_items: List[ConstructItemSchema]


class TextConstructSchema(BaseModel):
	id: uuid.UUID
	name: str
	desc: str
	type: uuid.UUID
	items: ConstructItemSchema


class PageMultiConstructSchema(BaseModel):
	page_id: uuid.UUID
	step_id: uuid.UUID
	order_position: int
	constructs: List[TextConstructSchema]


class ParticipantTypeSchema(BaseModel):
	id: uuid.UUID
	type: str

	model_config = ConfigDict(from_attributes=True)


class NewParticipantTypeSchema(BaseModel):
	type: str


class StepIdRequestSchema(BaseModel):
	current_step_id: uuid.UUID


# {
# 	'iss': 'https://dev-ezaapkd1uq45qy8u.us.auth0.com/',
# 	'sub': 'auth0|667f78dc16bf3a06dc53f472',
# 	'aud': ['https://rssa.recsys.dev/api/', 'https://dev-ezaapkd1uq45qy8u.us.auth0.com/userinfo'],
# 	'iat': 1721768272, 'exp': 1721854672,
# 	'scope': 'openid profile email',
# 	'azp': 'L1eKFXJ57zarQhNkGTEB0YfPHCokSQNI',
# 	'permissions': ['delete:all', 'read:all', 'write:all']
# 	}
