"""Pytest configuration and fixtures."""

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio

# Local imports
from httpx import ASGITransport, AsyncClient

# Import all models to ensure metadata is populated
from rssa_storage.rssadb.models.rssa_base_models import RssaBase as DBBaseModel
from rssa_storage.rssadb.models.study_components import Study, User

# Patch PostgreSQL ARRAY for SQLite
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import ARRAY, JSON

from rssa_api.data.sources.rssadb import rssa_db
from rssa_api.main import app


@compiles(ARRAY, 'sqlite')
def compile_array(element, compiler, **kw):
    """Compiles PostgreSQL ARRAY type to JSON for SQLite compatibility."""
    return 'JSON'


@compiles(postgresql.JSONB, 'sqlite')
def compile_jsonb(element, compiler, **kw):
    """Compiles PostgreSQL JSONB type to JSON for SQLite compatibility."""
    return 'JSON'


postgresql.JSONB = JSON

# Import the app
# Import all models to ensure metadata is populated


# SQLite in-memory database URL for testing
SQLALCHEMY_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Creates a test database engine (SQLite in-memory).

    Yields:
        AsyncEngine: The SQLAlchemy async engine.
    """
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )

    # Fix SQLite compatibility for UniqueConstraints
    for table in DBBaseModel.metadata.tables.values():
        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                constraint.deferrable = None
                constraint.initially = None

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(DBBaseModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(DBBaseModel.metadata.drop_all)


@pytest_asyncio.fixture(scope='function')
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Creates a new database session for a test.

    Rolls back the transaction after the test completes.

    Args:
        db_engine: The async database engine.

    Yields:
        AsyncSession: The database session.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(scope='function')
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Creates a robust AsyncClient for API testing.

    Overrides the database dependency to use the test session.

    Args:
        db_session: The test database session.

    Yields:
        AsyncClient: The HTTP client.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[rssa_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_user(db_session: AsyncSession) -> User:
    """Seeds a test user into the database.

    Args:
        db_session: The database session.

    Returns:
        User: The created user object.
    """
    user_id = uuid.uuid4()
    user = User(id=user_id, auth0_sub='auth0|testuser')
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def seed_study(db_session: AsyncSession, seed_user: User) -> Study:
    """Seeds a test study into the database.

    Args:
        db_session: The database session.
        seed_user: The study owner.

    Returns:
        Study: The created study object.
    """
    study_id = uuid.uuid4()
    study = Study(
        id=study_id,
        name='Test Study',
        description='Test Description',
        owner_id=seed_user.id,
        created_by_id=seed_user.id,
    )
    db_session.add(study)
    await db_session.commit()
    return study
