"""Socket-level execution timing; in-memory transports cannot detect read timeouts."""

import asyncio
import json

import pytest

from app.config import settings
from app.jobs.report_worker import generate_report

DIAGNOSTIC_SECONDS = 10.25


@pytest.mark.asyncio
async def test_worker_waits_for_a_real_http_diagnostic(monkeypatch):
    calls = []
    handlers = set()

    async def handle(reader, writer):
        task = asyncio.current_task()
        handlers.add(task)
        try:
            headers = await reader.readuntil(b"\r\n\r\n")
            size = next(int(line.split(b":", 1)[1]) for line in headers.splitlines()
                        if line.lower().startswith(b"content-length:"))
            calls.append(json.loads(await reader.readexactly(size)))
            await asyncio.sleep(DIAGNOSTIC_SECONDS)
            body = b'{"report_id":"slow-report","status":"complete"}'
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                         + f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            handlers.discard(task)

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    monkeypatch.setattr(settings, "INTERNAL_API_ORIGIN", f"http://127.0.0.1:{port}")
    try:
        async with server:
            await generate_report({}, "slow-report", "synthetic-job-token")
        assert calls == [{"report_id": "slow-report"}]
    finally:
        server.close()
        await server.wait_closed()
        await asyncio.gather(*handlers)
