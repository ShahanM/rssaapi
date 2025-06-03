import uuid
from typing import List, Optional

from pydantic import BaseModel


class EmotionsSchema(BaseModel):
	id: uuid.UUID
	movie_id: uuid.UUID
	movielens_id: str
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


class MovieSearchRequest(BaseModel):
	query: str


class MovieSearchResponse(BaseModel):
	exact_match: List[MovieSchema] = []
	near_matches: List[MovieSchema] = []
