"""ARQ worker that calls the API execution boundary over HTTP."""

import httpx

from app.jobs import report_client


async def generate_report(ctx, report_id: str, job_token: str):
    """
    ARQ worker function. It has no database session or pipeline import.

    Args:
        ctx: ARQ worker context; tests may supply an HTTP client adapter.
        report_id: UUID bound into the signed job token.
        job_token: short-lived service credential, never sent to a browser.
    """
    client = ctx.get("http_client") if isinstance(ctx, dict) else None
    if client is not None and not isinstance(client, httpx.AsyncClient):
        raise TypeError("Worker HTTP client must be an httpx.AsyncClient")
    await report_client.execute_report(report_id, job_token, client=client)
