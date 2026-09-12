"""Application service that persists one diagnostic pipeline execution."""

import asyncio

from app.database import async_session_factory
from app.repositories import report_runs


def _run_diagnostic(brand_input: dict[str, str]) -> dict:
    from engine.orchestrator import run_full_diagnostic

    return run_full_diagnostic(
        brand_name=brand_input["name"],
        website_url=brand_input["website_url"],
        industry=brand_input["industry"],
        competitor=brand_input["competitor"],
    )


SAFE_FAILURE_MESSAGE = "Analysis execution failed"


async def _mark_failed(report_id: str, user_id: str) -> None:
    """Persist a safe terminal state without exposing engine errors."""
    async with async_session_factory() as db:
        try:
            await report_runs.fail(db, report_id, user_id, SAFE_FAILURE_MESSAGE)
            await db.commit()
        except Exception:
            await db.rollback()


async def execute(brand_input: dict[str, str], user_id: str, report_id: str) -> str:
    """Claim, execute, and persist an internally authorized report run."""
    async with async_session_factory() as db:
        if not await report_runs.claim_queued(db, report_id, user_id):
            return "not_claimed"
        await db.commit()

    try:
        diagnostic = await asyncio.to_thread(_run_diagnostic, brand_input)
    except Exception:
        await _mark_failed(report_id, user_id)
        return "failed"

    completion_failed = False
    async with async_session_factory() as db:
        try:
            completed = await report_runs.complete(db, report_id, user_id, diagnostic)
            if not completed:
                await db.rollback()
                completion_failed = True
            else:
                await db.commit()
                return "complete"
        except Exception:
            await db.rollback()
            completion_failed = True

    if completion_failed:
        await _mark_failed(report_id, user_id)
        return "failed"

    return "failed"
