"""HTTP contract for the F04-A report submission and pipeline boundary."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1 import brands
from app.main import app
from app.services import report_pipeline


@pytest.mark.asyncio
async def test_submit_debits_once_and_pipeline_persists_through_public_api(monkeypatch):
    queued = []

    async def capture_enqueue(job):
        queued.append(job)

    monkeypatch.setattr(brands, "enqueue_report", capture_enqueue)
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer dev-user-f04-boundary"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        submission = await client.post("/api/v1/brands/analyze", headers=headers, json={
            "name": "Boundary Brand",
            "website_url": "https://boundary.example",
            "industry": "testing",
        })
        assert submission.status_code == 200
        report_id = submission.json()["data"]["report_id"]
        assert len(queued) == 1
        assert queued[0].report_id == report_id
        assert queued[0].brand_input["name"] == "Boundary Brand"

        credits = await client.get("/api/v1/credits", headers=headers)
        assert credits.status_code == 200
        assert credits.json()["data"]["balance"] == 24

        before = await client.get(f"/api/v1/reports/{report_id}", headers=headers)
        assert before.status_code == 200
        assert before.json()["data"]["status"] == "queued"

        monkeypatch.setattr(report_pipeline, "_run_diagnostic", lambda _: {
            "seo": {"score": 81},
            "geo": {"score": 72},
            "overall_score": 77,
            "_costs": [{"provider": "fixture", "cost_cents": 2, "duration_ms": 3}],
        })
        await report_pipeline.run(queued[0].brand_input, queued[0].user_id, report_id)

        completed = await client.get(f"/api/v1/reports/{report_id}", headers=headers)
        assert completed.status_code == 200
        payload = completed.json()["data"]
        assert payload["status"] == "complete"
        assert payload["scores"] == {"seo": 81, "geo": 72, "overall": 77}
        assert payload["payload"]["seo"]["score"] == 81
        assert "_costs" not in payload["payload"]


@pytest.mark.asyncio
async def test_worker_delegates_to_pipeline_service(monkeypatch):
    from app.jobs import report_worker

    received = []

    async def capture_run(brand_input, user_id, report_id):
        received.append((brand_input, user_id, report_id))

    monkeypatch.setattr(report_pipeline, "run", capture_run)
    await report_worker.generate_report(None, {"name": "Worker Brand"}, "owner-1", "report-1")
    assert received == [({"name": "Worker Brand"}, "owner-1", "report-1")]


def test_submit_operation_is_typed_and_described_in_openapi():
    operation = app.openapi()["paths"]["/api/v1/brands/analyze"]["post"]
    assert operation["summary"] == "Submit an owned brand analysis"
    assert "Reserves one credit" in operation["description"]
    assert "$ref" in operation["requestBody"]["content"]["application/json"]["schema"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/AnalyzeReportResponse"
    )
