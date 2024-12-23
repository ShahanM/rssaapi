from typing import Optional, Literal, List
from pydantic import BaseModel
from .movieschema import EmotionsSchema
from .movieschema import RatedItemSchema


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
	emotions: Optional[EmotionsSchema]
	poster_identifier: Optional[str]
	profile: Optional[AdvisorProfileSchema]
	status: Literal["Pending", "Accepted", "Rejected"]

	class Config:
		from_attributes = True


class AdvisorSchemaTemp(BaseModel):
	id: int
	name: str
	advice_preview: str
	advice: str
	profile: AdvisorProfileSchema
	rating: int
	status: Literal["Pending", "Accepted", "Rejected"]


class PrefCommRatingSchema(BaseModel):
	user_id: int
	ratings: List[RatedItemSchema]
	rec_type: int
	num_rec: int = 10

	class Config:
		from_attributes = True