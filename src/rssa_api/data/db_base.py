"""Database base components for asynchronous operations."""

from collections.abc import AsyncGenerator
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import rssa_api.config as cfg


def create_db_components(db_name_env_key: str, echo: bool = False):
    """Creates the async engine and session factory based on environment variables."""
    dbuser = cfg.get_env_var('DB_USER')
    dbpass = cfg.get_env_var('DB_PASSWORD')
    dbhost = cfg.get_env_var('DB_HOST')
    dbport = cfg.get_env_var('DB_PORT')
    dbname = cfg.get_env_var(db_name_env_key)

    db_url = f'postgresql+asyncpg://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}'

    engine = create_async_engine(db_url, echo=echo)
    session_factory = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

    return engine, session_factory


T = TypeVar('T')


class BaseDatabaseContext:
    """Generic Asynchronous context manager for Database sessions."""

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        self.session = self.session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()

    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        """Allows the instance to be used as a FastAPI Dependency."""
        session = self.session_factory()  # <--- Create LOCAL session
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def generic_get_db(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Generic generator to yield a database session."""
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
