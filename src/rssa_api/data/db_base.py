"""Database base components for asynchronous operations."""

from collections.abc import AsyncGenerator
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import rssa_api.core.config as cfg


def create_db_components(
    db_name_env_key: str,
    use_env_port: bool = False,
    use_neon_params: bool = False,
    echo: bool = False,
):
    """Creates the async engine and session factory based on environment variables."""
    dbuser = cfg.get_env_var('DB_USER')
    dbpass = cfg.get_env_var('DB_PASSWORD')
    dbhost = cfg.get_env_var('DB_HOST')
    dbport = cfg.get_env_var('DB_PORT')
    dbname = cfg.get_env_var(db_name_env_key)

    sslmode = cfg.get_env_var('DB_SSLMODE')
    channel = cfg.get_env_var('DB_CHANNELBINDING')

    db_url = f'postgresql+asyncpg://{dbuser}:{dbpass}@{dbhost}'

    if use_env_port:
        db_url = f'{db_url}:{dbport}'

    db_url = f'{db_url}/{dbname}'

    connect_args = {}
    if use_neon_params:
        # asyncpg specific connection arguments
        connect_args = {
            'ssl': sslmode,  # e.g. "require" or "verify-full"
            'server_settings': {'channel_binding': channel or 'prefer'},
        }
        # Fallback if the user wants to force it via URL, but connect_args is better for asyncpg
        # However, for simplicity and compatibility with existing env vars strings:
        if sslmode:
            connect_args['ssl'] = sslmode

    # Recommended settings for cloud databases (Neon, RDS, etc.)
    engine = create_async_engine(
        db_url,
        echo=echo,
        pool_pre_ping=True,  # Critical for handling severed connections
        pool_recycle=1800,  # Recycle connections every 30 minutes
        pool_size=20,
        max_overflow=10,
        connect_args=connect_args,
    )
    session_factory = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

    return engine, session_factory


T = TypeVar('T')


class BaseDatabaseContext:
    """Generic Asynchronous context manager for Database sessions."""

    def __init__(self, session_factory):
        """Initialize the database context with a session factory."""
        self.session_factory = session_factory
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        """Create a new database session."""
        self.session = self.session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the database session."""
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
