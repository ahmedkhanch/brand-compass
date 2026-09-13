"""Runner resource ownership and queue fallback contracts."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.config import settings
from app.jobs import dispatch, report_client, report_worker
from app.schemas.report_job import QueuedReport

JOB = QueuedReport("report", "synthetic-token", "boussole")


@pytest.mark.asyncio
async def test_missing_origin_never_creates_client(monkeypatch):
    monkeypatch.setattr(settings, "INTERNAL_API_ORIGIN", None)
    with pytest.raises(RuntimeError, match="not configured"):
        await report_client.execute_report(JOB.report_id, JOB.job_token)


@pytest.mark.asyncio
async def test_worker_rejects_an_invalid_client():
    with pytest.raises(TypeError, match="AsyncClient"):
        await report_worker.generate_report({"http_client": object()}, "report", "token")


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [200, 503])
async def test_borrowed_http_client_remains_open(monkeypatch, status):
    monkeypatch.setattr(settings, "INTERNAL_API_ORIGIN", "http://test")
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(status, json={"status": "complete"}),
    )) as client:
        if status == 503:
            with pytest.raises(httpx.HTTPStatusError):
                await report_client.execute_report("report", "token", client)
        else:
            await report_client.execute_report("report", "token", client)
        assert not client.is_closed


@pytest.mark.asyncio
@pytest.mark.parametrize("queue_fails", [False, True])
async def test_redis_pool_closed_and_failure_uses_fallback(monkeypatch, queue_fails):
    import arq

    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379")
    pool = SimpleNamespace(enqueue_job=AsyncMock(), aclose=AsyncMock())
    if queue_fails:
        pool.enqueue_job.side_effect = ConnectionError("queue offline")
    monkeypatch.setattr(arq, "create_pool", AsyncMock(return_value=pool))
    dispatched = []

    class InlineThread:
        def __init__(self, target, args, daemon):
            self.args = args

        def start(self):
            dispatched.append(self.args[0])

    monkeypatch.setattr(dispatch.threading, "Thread", InlineThread)
    await dispatch.enqueue_report(JOB)
    pool.aclose.assert_awaited_once()
    pool.enqueue_job.assert_awaited_once_with(
        "generate_report", report_id="report", job_token="synthetic-token",
    )
    assert dispatched == ([JOB] if queue_fails else [])


@pytest.mark.asyncio
async def test_local_fallback_invokes_http_adapter(monkeypatch):
    received = []

    async def execute(report_id, token):
        received.append((report_id, token))

    monkeypatch.setattr(report_client, "execute_report", execute)
    await asyncio.to_thread(dispatch._run_locally, JOB)
    assert received == [("report", "synthetic-token")]


@pytest.mark.asyncio
async def test_queue_cleanup_error_does_not_repeat_accepted_job(monkeypatch):
    import arq

    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379")
    pool = SimpleNamespace(enqueue_job=AsyncMock(), aclose=AsyncMock(side_effect=ConnectionError))
    monkeypatch.setattr(arq, "create_pool", AsyncMock(return_value=pool))
    await dispatch.enqueue_report(JOB)
    pool.enqueue_job.assert_awaited_once()
    pool.aclose.assert_awaited_once()
