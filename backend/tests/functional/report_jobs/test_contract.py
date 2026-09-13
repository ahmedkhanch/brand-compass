"""The execution API rejects callers before any report or provider access."""

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_execution_requires_job_authorization():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/internal/report-jobs/untrusted/execute",
            json={"report_id": "untrusted"},
        )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
