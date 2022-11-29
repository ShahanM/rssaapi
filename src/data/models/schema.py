from typing import List, Optional, Literal, Union
from pydantic import BaseModel


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
		orm_mode = True


class MovieSchema(BaseModel):
	id: int
	movie_id: str
	title: str
	year: int
	ave_rating: float
	genre: str
	director: Optional[str]
	cast: str
	description: str
	poster: str
	emotions: Optional[EmotionsSchema]

	class Config:
		orm_mode = True


class RatedItemSchema(BaseModel):
	item_id: int
	rating: int

	class Config:
		orm_mode = True


class RatingsSchema(BaseModel):
	user_id: int
	ratings: List[RatedItemSchema]
	rec_type: int
	num_rec: int = 10

	class Config:
		orm_mode = True


class EmotionContinuousInputSchema(BaseModel):
	emotion: str
	switch: Literal["ignore", "diverse", "specified"]
	weight: float


class EmotionDiscreteInputSchema(BaseModel):
	emotion: str
	weight: Literal["low", "high", "diverse", "ignore"]


class EmotionInputSchema(BaseModel):
	user_id: int
	input_type: Literal["discrete", "continuous"]
	emotion_input: Union[List[EmotionDiscreteInputSchema], \
		List[EmotionContinuousInputSchema]]
	ratings: List[RatedItemSchema]
	num_rec: int