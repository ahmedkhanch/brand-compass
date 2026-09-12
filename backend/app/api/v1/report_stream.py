"""SSE transport for owned progress; authorization completes before headers are sent."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_or_create_user
from app.schemas.common import ApiError, AUTH_RESPONSES
from app.services import report_progress

sse_router = APIRouter(tags=["reports"])


@sse_router.get("/sse/reports/{report_id}", response_class=StreamingResponse,
                summary="Follow your report progress",
                description="Authenticates and checks ownership before opening SSE. Each polling transaction is short and rechecks ownership. Emits status changes and ends on complete, failed, deletion or timeout.",
                responses={**AUTH_RESPONSES, 404: {"model": ApiError, "description": "Report absent or owned by another user."},
                           200: {"content": {"text/event-stream": {"schema": {"type": "string"}}}, "description": "SSE data frames containing report status."}})
async def stream_report_progress(report_id: str, request: Request,
                                 user: dict = Depends(get_or_create_user), db: AsyncSession = Depends(get_db)):
    await report_progress.require_owned_status(db, report_id, user["user_id"])
    return StreamingResponse(report_progress.events(request, report_id, user["user_id"]),
                             media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})
