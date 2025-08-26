import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import MOVIEDBBase as Base


class Movie(Base):
	__tablename__ = 'movies'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	movielens_id: Mapped[str] = mapped_column(unique=True)
	tmdb_id: Mapped[str] = mapped_column(nullable=True)
	imdb_id: Mapped[str] = mapped_column(nullable=False)
	title: Mapped[str] = mapped_column(nullable=False)
	year: Mapped[int] = mapped_column()
	runtime: Mapped[int] = mapped_column(default=0)
	genre: Mapped[str] = mapped_column()

	imdb_genres: Mapped[str] = mapped_column()
	tmdb_genres: Mapped[str] = mapped_column()

	ave_rating: Mapped[float] = mapped_column(default=0.0)

	imdb_avg_rating: Mapped[float] = mapped_column()
	imdb_rate_count: Mapped[int] = mapped_column()

	tmdb_avg_rating: Mapped[float] = mapped_column()
	tmdb_rate_count: Mapped[int] = mapped_column()

	movielens_avg_rating: Mapped[float] = mapped_column()
	movielens_rate_count: Mapped[int] = mapped_column()

	origin_country: Mapped[str] = mapped_column()

	parental_guide: Mapped[str] = mapped_column()

	movie_lens_dataset: Mapped[str] = mapped_column()
	last_updated: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)

	director: Mapped[str] = mapped_column(default='')
	writer: Mapped[str] = mapped_column(default='')
	description: Mapped[str] = mapped_column(default='')
	cast: Mapped[str] = mapped_column(default='')

	poster: Mapped[str] = mapped_column(default='')
	tmdb_poster: Mapped[str] = mapped_column()

	count: Mapped[int] = mapped_column(default=-1)

	rank: Mapped[int] = mapped_column(default=-1)

	imdb_popularity: Mapped[float] = mapped_column()
	tmdb_popularity: Mapped[float] = mapped_column()

	poster_identifier: Mapped[str] = mapped_column()

	emotions: Mapped[Optional['MovieEmotions']] = relationship(
		'MovieEmotions', back_populates='movie', cascade='all, delete-orphan', uselist=False
	)
	recommendations_text: Mapped[Optional['MovieRecommendationText']] = relationship(
		'MovieRecommendationText', back_populates='movie', cascade='all, delete-orphan', uselist=False
	)

	# All required fields are part of the Movielens dataset
	# All other fields need to be updated from TMDB and IMDB
	# def __init__(
	# 	self,
	# 	movielens_id: str,  # required
	# 	imdb_id: str,  # required
	# 	title: str,  # required
	# 	year: int,  # required
	# 	genre: str,  # required
	# 	runtime: int = 0,
	# 	ave_rating: float = 0,

	# 	director: str = '',
	# 	writer: str = '',
	# 	description: str = '',
	# 	cast: str = '',
	# 	poster: str = '',
	# 	count: int = -1,
	# 	rank: int = -1,
	# 	poster_identifier: str = '',
	# ):
	# 	self.movielens_id = movielens_id
	# 	self.imdb_id = imdb_id
	# 	self.title = title
	# 	self.year = year
	# 	self.runtime = runtime
	# 	self.genre = genre

	# 	self.ave_rating = ave_rating
	# 	self.director = director
	# 	self.writer = writer
	# 	self.description = description
	# 	self.cast = cast
	# 	self.poster = poster
	# 	self.count = count
	# 	self.rank = rank
	# 	self.poster_identifier = poster_identifier
	# 	self.last_updated = datetime.now(timezone.utc)


class MovieEmotions(Base):
	__tablename__ = 'movie_emotions'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	movie_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('movies.id'), nullable=False)
	movielens_id: Mapped[str] = mapped_column()
	anger: Mapped[float] = mapped_column()
	anticipation: Mapped[float] = mapped_column()
	disgust: Mapped[float] = mapped_column()
	fear: Mapped[float] = mapped_column()
	joy: Mapped[float] = mapped_column()
	surprise: Mapped[float] = mapped_column()
	sadness: Mapped[float] = mapped_column()
	trust: Mapped[float] = mapped_column()
	iers_count: Mapped[int] = mapped_column()
	iers_rank: Mapped[int] = mapped_column()

	movie = relationship('Movie', back_populates='emotions')

	# def __init__(
	# 	self,
	# 	movie_id: uuid.UUID,
	# 	movielens_id: str,
	# 	anger: float,
	# 	anticipation: float,
	# 	disgust: float,
	# 	fear: float,
	# 	joy: float,
	# 	surprise: float,
	# 	sadness: float,
	# 	trust: float,
	# 	iers_count: int,
	# 	iers_rank: int,
	# ):
	# 	self.movie_id = movie_id
	# 	self.movielens_id = movielens_id
	# 	self.anger = anger
	# 	self.anticipation = anticipation
	# 	self.disgust = disgust
	# 	self.fear = fear
	# 	self.joy = joy
	# 	self.surprise = surprise
	# 	self.sadness = sadness
	# 	self.trust = trust
	# 	self.iers_count = iers_count
	# 	self.iers_rank = iers_rank


class MovieRecommendationText(Base):
	__tablename__ = 'movie_recommendation_text'

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	movie_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('movies.id'), nullable=False)
	formal: Mapped[str] = mapped_column(nullable=True)
	informal: Mapped[str] = mapped_column(nullable=True)
	source: Mapped[str] = mapped_column(nullable=True)
	model: Mapped[str] = mapped_column(nullable=True)

	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
	)

	movie = relationship('Movie', back_populates='recommendations_text')

	# def __init__(self, movie_id: uuid.UUID, formal: str, informal: str, source: str, model: str):
	# 	self.movie_id = movie_id
	# 	self.formal = formal
	# 	self.informal = informal
	# 	self.source = source
	# 	self.model = model
