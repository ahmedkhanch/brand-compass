"""
ARQ worker entrypoint.
Per README §6.3: lightweight async task queue backed by Redis.

Usage:
  arq arq_worker.py  # requires Redis running

For local dev without Redis, the FastAPI backend runs jobs inline via BackgroundTasks.
"""

from arq import create_pool
from arq.connections import RedisSettings
from app.jobs.report_worker import generate_report
from app.config import settings


async def startup(ctx):
    """Worker startup — called once when the worker process starts."""
    ctx["app_name"] = settings.APP_NAME


async def shutdown(ctx):
    """Worker shutdown — cleanup connections."""
    pass


# Worker configuration
class WorkerSettings:
    functions = [generate_report]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL) if settings.REDIS_URL else None
    max_jobs = 10
    job_timeout = 300  # 5 minutes max per report
    keep_result = 3600  # Keep results for 1 hour
