"""SQLAlchemy session lifecycle. Schema creation belongs exclusively to Alembic."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    **({"connect_args": {"check_same_thread": False, "timeout": 5}} if is_sqlite else {
        "pool_size": 10, "max_overflow": 20, "pool_pre_ping": True, "pool_recycle": 3600
    }),
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db():
    await engine.dispose()
