"""Queue adapter for authorized report submissions."""

import threading

from app.config import settings
from app.jobs import report_client
from app.services.report_submission import QueuedReport


def _run_locally(job: QueuedReport) -> None:
    import asyncio

    async def run_after_submission_commit() -> None:
        # Preserve the historical delay that lets the request transaction commit
        # before the local runner reads the newly queued report.
        await asyncio.sleep(1)
        await report_client.execute_report(job.report_id, job.job_token)

    asyncio.run(run_after_submission_commit())


async def enqueue_report(job: QueuedReport) -> None:
    """Enqueue through ARQ when available, otherwise preserve the local runner."""
    if settings.REDIS_URL:
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
            pass

    threading.Thread(target=_run_locally, args=(job,), daemon=True).start()
