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
	source: Optional[str]
	model: Optional[str]
	created_at: datetime
	updated_at: datetime


class MovieSchema(BaseDBSchema):
	imdb_id: Optional[str]
	tmdb_id: Optional[str]
	movielens_id: str

	title: str
	year: int
	ave_rating: float

	imdb_avg_rating: Optional[float]
	imdb_rate_count: Optional[int]

	tmdb_avg_rating: Optional[float]
	tmdb_rate_count: Optional[int]

	genre: str
	director: Optional[str]
	cast: str
	description: str
	poster: str
	poster_identifier: Optional[str] = ''


class ERSMovieSchema(MovieSchema):
	emotions: EmotionsSchema


class MovieSearchRequest(BaseModel):
	query: str


class MovieSearchResponse(BaseModel):
	exact_match: List[MovieSchema] = []
	near_matches: List[MovieSchema] = []


class MovieDetailSchema(MovieSchema):
	emotions: Optional[EmotionsSchema] = None
	recommendations_text: Optional[RecommendationTextSchema] = None

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class PaginatedMovieList(BaseModel):
	data: list[MovieDetailSchema]
	count: int


class ReviewItem(BaseModel):
	text: str
	helpful: int
	unhelpful: int
	date: str


class ImdbReviewsPayloadSchema(BaseModel):
	imdb_id: str
	reviews: list[ReviewItem]
