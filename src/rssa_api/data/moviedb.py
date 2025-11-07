"""Asynchronous database session management for the Movie Database."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import rssa_api.config as cfg

dbuser = cfg.get_env_var('DB_USER')
dbpass = cfg.get_env_var('DB_PASSWORD')
dbhost = cfg.get_env_var('DB_HOST')
dbport = cfg.get_env_var('DB_PORT')
dbname = cfg.get_env_var('MOVIE_DB_NAME')

ASYNC_MOVIE_DB = f'postgresql+asyncpg://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}'
async_engine = create_async_engine(ASYNC_MOVIE_DB)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine, expire_on_commit=False)


class MovieDatabase:
    """Asynchronous context manager for Movie Database sessions.

    Usage:
        async with MovieDatabase() as session:
            # Use the session here

    Attributes:
        session (AsyncSession): The asynchronous database session.
    """

    async def __aenter__(self):
        """Enter the asynchronous context manager."""
        self.session = AsyncSessionLocal()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the asynchronous context manager."""
        await self.session.commit()
        await self.session.close()


async def get_db():
    """Asynchronous generator to yield a database session.

    Yields:
        AsyncSession: An asynchronous database session.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
