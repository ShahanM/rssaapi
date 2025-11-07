"""SQLAlchemy models for movies in the RSSA API."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Movie(DeclarativeBase):
    """SQLAlchemy model for the 'movies' table.

    Attributes:
        id (uuid.UUID): Primary key.
        movielens_id (str): Unique MovieLens identifier.
        tmdb_id (str): TMDB identifier.
        imdb_id (str): IMDB identifier.
        title (str): Title of the movie.
        year (int): Release year of the movie.
        runtime (int): Runtime of the movie in minutes.
        genre (str): Genre(s) of the movie.
        imdb_genres (str): Genres from IMDB.
        tmdb_genres (str): Genres from TMDB.
        ave_rating (float): Average rating across sources.
        imdb_avg_rating (float): Average rating from IMDB.
        imdb_rate_count (int): Number of ratings from IMDB.
        tmdb_avg_rating (float): Average rating from TMDB.
        tmdb_rate_count (int): Number of ratings from TMDB.
        movielens_avg_rating (float): Average rating from MovieLens.
        movielens_rate_count (int): Number of ratings from MovieLens.
        origin_country (str): Country of origin.
        parental_guide (str): Parental guidance information.
        movie_lens_dataset (str): Dataset source from MovieLens.
        last_updated (datetime): Timestamp of last update.
        director (str): Director(s) of the movie.
        writer (str): Writer(s) of the movie.
        description (str): Description or synopsis of the movie.
        cast (str): Cast members of the movie.
        poster (str): URL or path to the movie poster.
        tmdb_poster (str): TMDB poster URL or path.
        count (int): Count metric (context-specific).
        rank (int): Rank metric (context-specific).
        imdb_popularity (float): Popularity score from IMDB.
        tmdb_popularity (float): Popularity score from TMDB.
        poster_identifier (str): Identifier for the poster image.
    """

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


class MovieEmotions(DeclarativeBase):
    """SQLAlchemy model for the 'movie_emotions' table.

    Attributes:
        id (uuid.UUID): Primary key.
        movie_id (uuid.UUID): Foreign key to the movie.
        movielens_id (str): Unique MovieLens identifier.
        anger (float): Anger emotion score.
        anticipation (float): Anticipation emotion score.
        disgust (float): Disgust emotion score.
        fear (float): Fear emotion score.
        joy (float): Joy emotion score.
        surprise (float): Surprise emotion score.
        sadness (float): Sadness emotion score.
        trust (float): Trust emotion score.
        iers_count (int): IERS count metric.
        iers_rank (int): IERS rank metric.
    """

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


class MovieRecommendationText(DeclarativeBase):
    """SQLAlchemy model for the 'movie_recommendation_text' table.

    Attributes:
        id (uuid.UUID): Primary key.
        movie_id (uuid.UUID): Foreign key to the movie.
        formal (str): Formal recommendation text.
        informal (str): Informal recommendation text.
        source (str): Source of the recommendation.
        model (str): Model used for generating the recommendation.
    """

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
