"""Async SQLAlchemy engine + session. SQLite for dev, PostgreSQL for production."""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# SQLite pragmas: WAL lets readers (the SSE progress loop) and the writer (the
# report pipeline thread) run concurrently without blocking each other; a busy
# timeout absorbs the brief overlap instead of raising "database is locked".
_SQLITE_BUSY_TIMEOUT_MS = 5000

_IS_SQLITE = "sqlite" in settings.DATABASE_URL

_connect_args = {}
_engine_kwargs = {}

if _IS_SQLITE:
    # SQLite needs check_same_thread for async access
    _connect_args = {"check_same_thread": False}
else:
    # PostgreSQL connection pooling
    _engine_kwargs = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=_connect_args,
    **_engine_kwargs,
)

if _IS_SQLITE:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute(f"PRAGMA busy_timeout={_SQLITE_BUSY_TIMEOUT_MS}")
            cur.execute("PRAGMA synchronous=NORMAL")
        finally:
            cur.close()


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables. Called at app startup.
    Uses CREATE TABLE IF NOT EXISTS — safe for both SQLite and PostgreSQL.
    For production, use Alembic migrations instead."""
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose engine. Called at app shutdown."""
    await engine.dispose()
