from typing import List, Optional, Literal, Union
import pydantic
print(pydantic.__version__)
from pydantic import BaseModel, Field, AliasChoices
import uuid


class EmotionsSchema(BaseModel):
	id: int
	anger: float
	anticipation: float
	disgust: float
	fear: float
	joy: float
	surprise: float
	sadness: float
	trust: float

	class Config:
		from_attributes = True


class MovieSchema(BaseModel):
	id: int
	movie_id: int
	title: str
	year: int
	ave_rating: float
	genre: str
	director: Optional[str]
	cast: str
	description: str
	poster: str
	emotions: Optional[EmotionsSchema] = None
	poster_identifier: Optional[str]

	class Config:
		from_attributes = True


class MovieSchemaV2(BaseModel):
	id: uuid.UUID
	tmdb_id: str
	movielens_id: str
	title: str
	year: int
	ave_rating: float
	genre: str
	director: Optional[str]
	cast: str
	description: str
	poster: str
	emotions: Optional[EmotionsSchema] = None
	poster_identifier: Optional[str]

	class Config:
		from_attributes = True


class RatedItemSchema(BaseModel):
	item_id: int = Field(validation_alias=AliasChoices("movie_id", "item_id"))
	rating: int

	class Config:
		from_attributes = True


class RatingsSchema(BaseModel):
	user_id: int
	user_condition: int
	ratings: List[RatedItemSchema]
	rec_type: int
	num_rec: int = 10

	class Config:
		from_attributes = True


class RatingSchemaV2(BaseModel):
	user_id: uuid.UUID
	user_condition: uuid.UUID;
	ratings: List[RatedItemSchema]
	rec_type: int
	num_rec: int = 10


class EmotionContinuousInputSchema(BaseModel):
	emotion: str
	switch: Literal["ignore", "diverse", "specified"]
	weight: float


class EmotionDiscreteInputSchema(BaseModel):
	emotion: str
	weight: Literal["low", "high", "diverse", "ignore"]


class EmotionInputSchema(BaseModel):
	user_id: int
	user_condition: int
	input_type: Literal["discrete", "continuous"]
	emotion_input: Union[List[EmotionDiscreteInputSchema], \
		List[EmotionContinuousInputSchema]]
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
	input_type: Literal["discrete", "continuous"]
	emotion_input: Union[List[EmotionDiscreteInputSchema], \
		List[EmotionContinuousInputSchema]]
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
