"""Repository handling of reports removed while diagnostics are in flight."""

from unittest.mock import AsyncMock

import pytest

from app.repositories import report_runs


@pytest.mark.asyncio
async def test_missing_owned_report_cannot_be_completed_or_failed(monkeypatch):
    db = AsyncMock()
    monkeypatch.setattr(report_runs.reports, "owned", AsyncMock(return_value=None))
    assert not await report_runs.complete(db, "removed-report", "owner", {})
    assert not await report_runs.fail(db, "removed-report", "owner", "safe error")
    db.flush.assert_not_awaited()
