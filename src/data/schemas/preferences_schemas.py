import uuid
from typing import List, Literal, Optional, Union

from pydantic import BaseModel


class RatedItemSchema(BaseModel):
	item_id: int
	rating: int

	def __hash__(self):
		return self.model_dump_json().__hash__()


class PrefVizItem(BaseModel):
	item_id: str
	community_score: float
	user_score: float
	community_label: int
	user_label: int
	cluster: int = 0


class PrefVizDemoRequestSchema(BaseModel):
	user_id: int
	user_condition: int
	ratings: List[RatedItemSchema]
	num_rec: int = 10
	algo: str
	randomize: bool
	init_sample_size: int
	min_rating_count: int

	class Config:
		from_attributes = True

	def __hash__(self):
		return self.model_dump_json().__hash__()


class PreferenceRequestSchema(BaseModel):
	user_id: uuid.UUID
	user_condition: uuid.UUID
	is_baseline: bool = False
	ratings: List[RatedItemSchema]

	def __hash__(self):
		return self.model_dump_json().__hash__()


class PrefVizMetadata(BaseModel, frozen=True):
	algo: str
	randomize: bool
	init_sample_size: int
	min_rating_count: int
	num_rec: int


class PrefVizDemoResponseSchema(BaseModel):
	metadata: PrefVizMetadata
	recommendations: List[PrefVizItem]

	class Config:
		from_attributes = True

	def __hash__(self):
		return self.model_dump_json().__hash__()


class PrefVizResponseSchema(BaseModel):
	metadata: PrefVizMetadata
	recommendations: List[PrefVizItem]

	def __hash__(self):
		return self.model_dump_json().__hash__()


class EmotionContinuousInputSchema(BaseModel):
	emotion: str
	switch: Literal['ignore', 'diverse', 'specified']
	weight: float


class EmotionDiscreteInputSchema(BaseModel):
	emotion: str
	weight: Literal['low', 'high', 'diverse', 'ignore']


class EmotionInputSchema(BaseModel):
	user_id: int
	user_condition: int
	input_type: Literal['discrete', 'continuous']
	emotion_input: Union[List[EmotionDiscreteInputSchema], List[EmotionContinuousInputSchema]]
	ratings: List[RatedItemSchema]
	num_rec: int


class RatingSchemaExperimental(BaseModel):
	user_id: int
	user_condition: int
	ratings: List[RatedItemSchema]
	rec_type: int
	num_rec: int = 10
	low_val: float = 0.3
	high_val: float = 0.8


class EmotionInputSchemaExperimental(BaseModel):
	user_id: int
	condition_algo: int
	input_type: Literal['discrete', 'continuous']
	emotion_input: Union[List[EmotionDiscreteInputSchema], List[EmotionContinuousInputSchema]]
	ratings: List[RatedItemSchema]
	num_rec: int
	item_pool_size: int
	scale_vector: bool = False
	low_val: float = 0.3
	high_val: float = 0.8
	algo: str
	dist_method: str
	diversity_criterion: str
	diversity_sample_size: Optional[int]


class AdvisorProfileSchema(BaseModel):
	likes: str
	dislikes: str
	most_rated_genre: str
	genretopten: str
	genre_with_least_rating: str


class AdvisorSchema(BaseModel):
	id: int
	movie_id: int
	name: str
	year: int
	ave_rating: float
	genre: str
	director: Optional[str]
	cast: str
	description: str
	poster: str
	poster_identifier: Optional[str]
	profile: Optional[AdvisorProfileSchema]
	status: Literal['Pending', 'Accepted', 'Rejected']

	class Config:
		from_attributes = True


class AdvisorSchemaTemp(BaseModel):
	id: int
	name: str
	advice_preview: str
	advice: str
	profile: AdvisorProfileSchema
	rating: int
	status: Literal['Pending', 'Accepted', 'Rejected']


class PrefCommRatingSchema(BaseModel):
	user_id: str
	ratings: List[RatedItemSchema]
	user_condition: str
	num_rec: int = 10

	class Config:
		from_attributes = True
