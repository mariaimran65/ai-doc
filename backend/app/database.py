import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

_db_host = os.getenv('DB_HOST') or 'db'
_db_port = os.getenv('DB_PORT') or '5432'
_db_user = os.getenv('DB_USER') or 'aidoc'
_db_name = os.getenv('DB_NAME') or 'aidoc'
_db_password = os.getenv('DB_PASSWORD') or 'aidoc'

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).info(
    "DB connection target: %s@%s:%s/%s", _db_user, _db_host, _db_port, _db_name
)

DATABASE_URL = (
    f"postgresql+asyncpg://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
