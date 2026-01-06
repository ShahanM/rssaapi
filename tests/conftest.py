import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from sqlalchemy.types import TypeDecorator, JSON

# Patch PostgreSQL ARRAY for SQLite
from sqlalchemy.dialects import postgresql

class MockARRAY(TypeDecorator):
    impl = JSON
    cache_ok = True
    
    def __init__(self, item_type, as_tuple=False, dimensions=None, zero_indexes=False):
        super().__init__()
        self.item_type = item_type

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value

postgresql.ARRAY = MockARRAY
postgresql.JSONB = JSON

# Import the app
from rssa_api.main import app
from rssa_api.data.rssadb import get_db
from rssa_api.data.models.rssa_base_models import DBBaseModel
from sqlalchemy.schema import UniqueConstraint

# Import all models to ensure metadata is populated
from rssa_api.data.models import (
    movies,
    participant_movie_sequence,
    participant_responses,
    study_components,
    study_participants,
    survey_constructs,
)

# SQLite in-memory database URL for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

import pytest_asyncio

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_engine():
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
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

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    connection = await db_engine.connect()
    transaction = await connection.begin()
    
    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()
    
    yield session
    
    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

import uuid
from rssa_api.data.models.study_components import User, Study

@pytest_asyncio.fixture
async def seed_user(db_session):
    user_id = uuid.uuid4()
    user = User(id=user_id, auth0_sub="auth0|testuser")
    db_session.add(user)
    await db_session.commit()
    return user

@pytest_asyncio.fixture
async def seed_study(db_session, seed_user):
    study_id = uuid.uuid4()
    study = Study(
        id=study_id, 
        name="Test Study", 
        description="Test Description", 
        owner_id=seed_user.id,
        created_by_id=seed_user.id
    )
    db_session.add(study)
    await db_session.commit()
    return study
