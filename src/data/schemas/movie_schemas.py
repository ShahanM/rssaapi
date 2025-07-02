import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from data.schemas.base_schemas import BaseDBSchema


class EmotionsSchema(BaseDBSchema):
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


class RecommendationTextSchema(BaseDBSchema):
	movie_id: uuid.UUID
	formal: str
	informal: str
	source: str
	model: str
	created_at: datetime
	updated_at: datetime


class MovieSchema(BaseDBSchema):
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
	# emotions: Optional[EmotionsSchema] = None
	# recommendations_text: Optional[RecommendationTextSchema] = None
	poster_identifier: Optional[str] = ''


class MovieSearchRequest(BaseModel):
	query: str


class MovieSearchResponse(BaseModel):
	exact_match: List[MovieSchema] = []
	near_matches: List[MovieSchema] = []
