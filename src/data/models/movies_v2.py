from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
import uuid
from datetime import datetime, timezone
from data.moviedb import Base


class Movie(Base):
	__tablename__ = 'movies'

	id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	movielens_id = sa.Column(sa.String, nullable=False, unique=True)
	tmdb_id = sa.Column(sa.String, nullable=True)
	imdb_id = sa.Column(sa.String, nullable=False)
	title = sa.Column(sa.String, nullable=False)
	year = sa.Column(sa.Integer, nullable=False)
	runtime = sa.Column(sa.Integer, nullable=False)
	genre = sa.Column(sa.String, nullable=False)
	ave_rating = sa.Column(sa.Numeric, nullable=False)
	director = sa.Column(sa.Text, nullable=False)
	writer = sa.Column(sa.Text, nullable=False)
	description = sa.Column(sa.Text, nullable=False)
	cast = sa.Column(sa.Text, nullable=False)
	poster = sa.Column(sa.String, nullable=False)
	count = sa.Column(sa.Integer, nullable=False)
	rank = sa.Column(sa.Integer, nullable=False)
	poster_identifier = sa.Column(sa.String, nullable=False)

	def __init__(self, movielens_id: str, tmdb_id: str, imdb_id: str,
		title: str, year: int, runtime: int, genre: str, ave_rating: float,
		director: str, writer: str, description: str, cast: str, poster: str,
		count: int, rank: int, poster_identifier: str = ''):
		self.movielens_id = movielens_id
		self.tmdb_id = tmdb_id
		self.imdb_id = imdb_id
		self.title = title
		self.year = year
		self.runtime = runtime
		self.genre = genre
		self.ave_rating = ave_rating
		self.director = director
		self.writer = writer
		self.description = description
		self.cast = cast
		self.poster = poster
		self.count = count
		self.rank = rank
		self.poster_identifier = poster_identifier


class MovieEmotions(Base):
	__tablename__ = 'movie_emotions'

	id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	movie_id = sa.Column(UUID(as_uuid=True), nullable=False, unique=True)
	movielens_id = sa.Column(sa.String, nullable=False)
	anger = sa.Column(sa.Numeric, nullable=False)
	anticipation = sa.Column(sa.Numeric, nullable=False)
	disgust = sa.Column(sa.Numeric, nullable=False)
	fear = sa.Column(sa.Numeric, nullable=False)
	joy = sa.Column(sa.Numeric, nullable=False)
	surprise = sa.Column(sa.Numeric, nullable=False)
	sadness = sa.Column(sa.Numeric, nullable=False)
	trust = sa.Column(sa.Numeric, nullable=False)
	iers_count = sa.Column(sa.Integer, nullable=False)
	iers_rank = sa.Column(sa.Integer, nullable=False)

	sa.ForeignKeyConstraint(['movie_id'], ['movies.id'])

	def __init__(self, movie_id: UUID, movielens_id:str, anger: float, anticipation: float,
		disgust: float, fear: float, joy: float, surprise: float,
		sadness: float, trust: float, iers_count: int, iers_rank: int):
		self.movie_id = movie_id
		self.movielens_id = movielens_id
		self.anger = anger
		self.anticipation = anticipation
		self.disgust = disgust
		self.fear = fear
		self.joy = joy
		self.surprise = surprise
		self.sadness = sadness
		self.trust = trust
		self.iers_count = iers_count
		self.iers_rank = iers_rank


class MovieRecommendationText(Base):
	__tablename__ = 'movie_recommendation_text'

	id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

	movie_id = sa.Column(UUID(as_uuid=True), nullable=False, unique=True)
	formal = sa.Column(sa.String, nullable=False)
	informal = sa.Column(sa.String, nullable=False)

	created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
	updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

	sa.ForeignKeyConstraint(['movie_id'], ['movies.id'])

	def __init__(self, movie_id: UUID, formal: str, informal: str):
		self.movie_id = movie_id
		self.formal = formal
		self.informal = informal