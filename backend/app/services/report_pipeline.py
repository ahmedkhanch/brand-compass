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


async def run(brand_input: dict[str, str], user_id: str, report_id: str) -> None:
    """Run a diagnostic and persist only the matching owner's state transitions."""
    async with async_session_factory() as db:
        if not await report_runs.mark_running(db, report_id, user_id):
            return
        await db.commit()

    try:
        diagnostic = await asyncio.to_thread(_run_diagnostic, brand_input)
    except Exception as exc:
        async with async_session_factory() as db:
            await report_runs.fail(db, report_id, user_id, str(exc))
            await db.commit()
        return

    async with async_session_factory() as db:
        await report_runs.complete(db, report_id, user_id, diagnostic)
        await db.commit()
