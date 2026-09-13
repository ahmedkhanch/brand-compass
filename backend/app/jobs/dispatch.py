"""Queue adapter for authorized report submissions."""

import threading
import logging

from app.config import settings
from app.jobs import report_client
from app.schemas.report_job import QueuedReport

logger = logging.getLogger(__name__)


def _run_locally(job: QueuedReport) -> None:
    import asyncio

    asyncio.run(report_client.execute_report(job.report_id, job.job_token))


async def enqueue_report(job: QueuedReport) -> None:
    """Enqueue through ARQ when available, otherwise preserve the local runner."""
    if settings.REDIS_URL:
        pool = None
        try:
            from arq import create_pool
            from arq.connections import RedisSettings

            pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
            await pool.enqueue_job(
                "generate_report",
                report_id=job.report_id,
                job_token=job.job_token,
            )
            return
        except Exception:
            logger.warning("Report queue unavailable; using local HTTP runner")
        finally:
            if pool is not None:
                try:
                    await pool.aclose()
                except Exception:
                    logger.warning("Report queue connection cleanup failed")

    threading.Thread(target=_run_locally, args=(job,), daemon=True).start()
