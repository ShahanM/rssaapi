from dataclasses import dataclass
from sqlalchemy import Column, Integer, Text, String, ForeignKey, Index, \
	Numeric
from sqlalchemy.orm import relationship
from data.moviedatabase import Base


class RankGroup(Base):
	__tablename__ = 'rank_group'

	id = Column(Integer, primary_key=True, autoincrement=True)
	group_label = Column(String(144), nullable=False)


class Movie(Base):
	__tablename__ = 'movie'

	id = Column(Integer, primary_key=True, autoincrement=True)

	movie_id = Column(Integer, nullable=False, unique=True)
	imdb_id = Column(String(144), nullable=False)
	title_year = Column(String(234), nullable=False)
	title = Column(String(234), nullable=False)
	year = Column(Integer, nullable=False)
	runtime = Column(Integer, nullable=False)
	genre = Column(String(144), nullable=False)
	ave_rating = Column(Numeric, nullable=False)
	director = Column(Text, nullable=False)
	writer = Column(Text, nullable=False)
	description = Column(Text, nullable=False)
	cast = Column(Text, nullable=False)
	poster = Column(String(234), nullable=False)
	count = Column(Integer, nullable=False)
	rank = Column(Integer, nullable=False)
	poster_identifier = Column(String(255), nullable=False)

	rank_group = Column('rank_group', ForeignKey('rank_group.id'))
	rank_group_idx = Index(rank_group, postgresql_using='hash')

	year_bucket = Column(Integer, nullable=False)
	year_bucket_idx = Index(year_bucket, postgresql_using='hash')

	movie_id_idx = Index(movie_id, postgresql_using='tree')

	emotions = relationship('MovieEmotions', back_populates='movie', \
		uselist=False)
	recommendation_text = relationship('MovieRecommendationText', \
		back_populates='movie', uselist=False)

	def __hash__(self):
		return hash(self.movie_id)


class MovieEmotions(Base):
	__tablename__ = 'movie_emotions'

	id = Column(Integer, primary_key=True, autoincrement=True)

	movie_id = Column(Integer, ForeignKey('movie.id'), \
		nullable=False, unique=True)

	anger = Column(Numeric, nullable=False)
	anticipation = Column(Numeric, nullable=False)
	disgust = Column(Numeric, nullable=False)
	fear = Column(Numeric, nullable=False)
	joy = Column(Numeric, nullable=False)
	surprise = Column(Numeric, nullable=False)
	sadness = Column(Numeric, nullable=False)
	trust = Column(Numeric, nullable=False)
	iers_count = Column(Integer, nullable=False)
	iers_rank = Column(Integer, nullable=False)

	iers_rank_group = Column('rank_group', ForeignKey('rank_group.id'))
	iers_rank_group_idx = Index(iers_rank_group, postgresql_using='hash')

	movie = relationship('Movie', back_populates='emotions')


class MovieRecommendationText(Base):
	__tablename__ = "movie_recommendation_text"

	id = Column(Integer, primary_key=True, autoincrement=True)

	movie_id = Column(Integer, ForeignKey('movie.id'), \
		nullable=False, unique=True)
	
	formal = Column(Text, nullable=False)
	informal = Column(Text, nullable=False)

	movie = relationship('Movie', back_populates='recommendation_text')

