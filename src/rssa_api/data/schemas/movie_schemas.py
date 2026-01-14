"""Movie related schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from rssa_api.data.schemas.base_schemas import DBMixin


class EmotionsSchema(DBMixin):
    """Schema for movie emotions."""

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


class RecommendationTextSchema(DBMixin):
    """Schema for recommendation text associated with a movie."""

    movie_id: uuid.UUID
    formal: str
    informal: str
    source: str | None
    model: str | None
    created_at: datetime
    updated_at: datetime


class MovieSchema(DBMixin):
    """Base schema for a Movie."""

    imdb_id: str | None
    tmdb_id: str | None
    movielens_id: str

    title: str
    year: int
    ave_rating: float

    imdb_avg_rating: float | None
    imdb_rate_count: int | None

    tmdb_avg_rating: float | None
    tmdb_rate_count: int | None

    genre: str
    director: str | None
    cast: str
    description: str
    poster: str
    tmdb_poster: str | None = ''
    poster_identifier: str | None = ''


class ERSMovieSchema(MovieSchema):
    """Movie schema including emotions."""

    emotions: EmotionsSchema


class MovieSearchRequest(BaseModel):
    """Request schema for searching movies."""

    query: str


class MovieSearchResponse(BaseModel):
    """Response schema for movie search results."""

    exact_match: list[MovieSchema] = []
    near_matches: list[MovieSchema] = []


class MovieDetailSchema(MovieSchema):
    """Detailed movie schema including emotions and recommendation text."""

    emotions: EmotionsSchema | None = None
    recommendations_text: RecommendationTextSchema | None = None


class PaginatedMovieList(BaseModel):
    """Schema for a paginated list of movies."""

    data: list[MovieDetailSchema]
    count: int


class ReviewItem(BaseModel):
    """Schema for a single movie review."""

    text: str
    helpful: int
    unhelpful: int
    date: str


class ImdbReviewsPayloadSchema(BaseModel):
    """Payload schema for IMDB reviews."""

    imdb_id: str
    reviews: list[ReviewItem]
