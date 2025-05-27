# from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

import config as cfg

dbuser = cfg.get_env_var('DB_USER')
dbpass = cfg.get_env_var('DB_PASSWORD')
dbhost = cfg.get_env_var('DB_HOST')
dbport = cfg.get_env_var('DB_PORT')
dbname = cfg.get_env_var('MOVIE_DB_NAME')

ASYNC_MOVIE_DB = f'postgresql+asyncpg://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}'
async_engine = create_async_engine(ASYNC_MOVIE_DB)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)


Base = declarative_base()


class MovieDatabase:
	async def __aenter__(self):
		self.session = AsyncSessionLocal()
		return self.session

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		await self.session.commit()
		await self.session.close()

	async def get_db(self):
		async with self:
			yield self.session


movie_db = MovieDatabase()
