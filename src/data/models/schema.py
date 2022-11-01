from typing import List, Optional
from pydantic import BaseModel

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

	class Config:
		orm_mode = True

class MovieEmotionSchema(MovieSchema):
	id: int
	movie_id: int
	anger: float
	contempt: float
	disgust: float
	fear: float
	happiness: float
	neutral: float
	sadness: float
	surprise: float

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
	numRec: int = 10

	class Config:
		orm_mode = True