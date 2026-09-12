"""Short, owned read transactions for the API's SSE lifecycle."""
import asyncio
import json
from fastapi import HTTPException
from app.database import async_session_factory
from app.repositories import reports

POLL_SECONDS = 1
MAX_POLLS = 180


async def read_status(report_id: str, user_id: str):
    async with async_session_factory() as db:
        result = await reports.status(db, report_id, user_id)
        return result.value if result is not None else None


async def require_owned_status(db, report_id: str, user_id: str):
    if await reports.status(db, report_id, user_id) is None:
        raise HTTPException(404, "Report not found")
    # Release the request transaction before opening a long-lived response.
    await db.rollback()


async def events(request, report_id: str, user_id: str):
    previous = None
    for _ in range(MAX_POLLS):
        if await request.is_disconnected():
            return
        status = await read_status(report_id, user_id)
        if status is None:
            yield 'data: {"status": "error", "message": "Report not found"}\n\n'
            return
        if status != previous:
            yield f"data: {json.dumps({'status': status, 'report_id': report_id})}\n\n"
            previous = status
        if status in {"complete", "failed"}:
            return
        await asyncio.sleep(POLL_SECONDS)
    yield 'data: {"status": "timeout", "message": "Report took too long"}\n\n'
