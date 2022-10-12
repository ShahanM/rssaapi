from dataclasses import dataclass
from sqlalchemy import Column, Integer, Text, String, ForeignKey, Index, \
	Numeric
from sqlalchemy.orm import relationship
from data.database import Base


@dataclass
class RankGroup(Base):
	__tablename__ = 'rank_group'

	id:int = Column(Integer, primary_key=True, autoincrement=True)
	group_label:str = Column(String(144), nullable=False)


@dataclass
class Movie(Base):
	__tablename__ = 'movie'

	id:int = Column(Integer, primary_key=True, autoincrement=True)

	movie_id:int = Column(Integer, nullable=False, unique=True)
	imdb_id:str = Column(String(144), nullable=False)
	title_year:str = Column(String(234), nullable=False)
	title:str = Column(String(234), nullable=False)
	year:int = Column(Integer, nullable=False)
	runtime:int = Column(Integer, nullable=False)
	genre:str = Column(String(144), nullable=False)
	ave_rating:float = Column(Numeric, nullable=False)
	director:str = Column(Text, nullable=False)
	writer:str = Column(Text, nullable=False)
	description:str = Column(Text, nullable=False)
	cast:str = Column(Text, nullable=False)
	poster:str = Column(String(234), nullable=False)
	count:int = Column(Integer, nullable=False)
	rank:int = Column(Integer, nullable=False)

	rank_group:RankGroup = Column('rank_group', ForeignKey('rank_group.id'))
	rank_group_idx = Index(rank_group, postgresql_using='hash')

	year_bucket:int = Column(Integer, nullable=False)
	year_bucket_idx = Index(year_bucket, postgresql_using='hash')

	movie_id_idx = Index(movie_id, postgresql_using='tree')

	emotions = relationship('MovieEmotions', back_populates='movie', \
		uselist=False)

	def __hash__(self):
		return hash(self.movie_id)

@dataclass
class MovieEmotions(Base):
	__tablename__ = 'movie_emotions'

	id:int = Column(Integer, primary_key=True, autoincrement=True)

	movie_id = Column(Integer, ForeignKey('movie.id'), \
		nullable=False, unique=True)

	anger:float = Column(Numeric, nullable=False)
	anticipation:float = Column(Numeric, nullable=False)
	disgust:float = Column(Numeric, nullable=False)
	fear:float = Column(Numeric, nullable=False)
	joy:float = Column(Numeric, nullable=False)
	surprise:float = Column(Numeric, nullable=False)
	sadness:float = Column(Numeric, nullable=False)
	trust:float = Column(Numeric, nullable=False)
	iers_count:int = Column(Integer, nullable=False)
	iers_rank:int = Column(Integer, nullable=False)

	iers_rank_group:RankGroup = Column('rank_group', ForeignKey('rank_group.id'))
	iers_rank_group_idx = Index(iers_rank_group, postgresql_using='hash')

	movie = relationship('Movie', back_populates='emotions')