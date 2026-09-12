"""HTTP adapter used by queue runners to request internal report execution."""

import httpx

from app.config import settings


async def execute_report(
    report_id: str,
    job_token: str,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Call the API boundary; workers never import database-backed services."""
    if not settings.INTERNAL_API_ORIGIN:
        raise RuntimeError("Internal report API origin is not configured")

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=settings.INTERNAL_API_TIMEOUT_SECONDS)

    try:
        response = await client.post(
            f"{settings.INTERNAL_API_ORIGIN.rstrip('/')}/api/v1/internal/report-jobs/{report_id}/execute",
            json={"report_id": report_id},
            headers={"Authorization": f"Bearer {job_token}"},
        )
        response.raise_for_status()
    finally:
        if owns_client:
            await client.aclose()
