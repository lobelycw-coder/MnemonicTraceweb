from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .config import settings
from .models import Base

engine = create_async_engine(settings().database_url.replace("postgres://", "postgresql+asyncpg://"))
Session = async_sessionmaker(engine, expire_on_commit=False)

@asynccontextmanager
async def session():
    async with Session() as s: yield s

async def init_db():
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)