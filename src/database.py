from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.settings import settings


DB_URL = settings.DB_URL

engine = create_async_engine(DB_URL)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with Session() as session:
        yield session


class Base(DeclarativeBase):
    pass
