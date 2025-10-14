from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import core.config as cfg

dbuser = cfg.get_env_var('DB_USER')
dbpass = cfg.get_env_var('DB_PASSWORD')
dbhost = cfg.get_env_var('DB_HOST')
dbport = cfg.get_env_var('DB_PORT')
dbname = cfg.get_env_var('RSSA_DB_NAME')

ASYNC_RSSA_DB = f'postgresql+asyncpg://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}'
async_engine = create_async_engine(ASYNC_RSSA_DB, echo=False)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine, expire_on_commit=False)


class RSSADatabase:
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.commit()
        await self.session.close()


async def get_db():
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
