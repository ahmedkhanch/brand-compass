"""HTTP authorization and execution checks for signed report jobs."""

import asyncio
import json
import time

import jwt
import pytest
import httpx

from app.adapters import report_job_token
from app.api.v1 import brands
from app.config import settings
from app.main import app
from app.services import report_pipeline

TEST_SECRET = "isolated-report-job-signing-secret-for-tests-only"
BRAND_INPUT = {
    "name": "Internal Execution Brand",
    "website_url": "https://internal.example",
    "industry": "testing",
    "competitor": "",
}


@pytest.fixture(autouse=True)
def job_configuration(monkeypatch):
    monkeypatch.setattr(settings, "REPORT_JOB_SECRET", TEST_SECRET)
    monkeypatch.setattr(settings, "INTERNAL_API_ORIGIN", "http://test")
    monkeypatch.setattr(settings, "REPORT_JOB_TOKEN_TTL_SECONDS", 300)


@pytest.fixture
def pipeline_calls(monkeypatch):
    calls = []

    async def capture(*args):
        calls.append(args)
        return "complete"

    monkeypatch.setattr(report_pipeline, "execute", capture)
    return calls


@pytest.fixture
def submit_job(monkeypatch, client):
    queued = []

    async def capture_enqueue(job):
        queued.append(job)

    monkeypatch.setattr(brands, "enqueue_report", capture_enqueue)

    async def submit(owner):
        headers = {"Authorization": f"Bearer dev-user-{owner}"}
        response = await client.post("/api/v1/brands/analyze", headers=headers, json=BRAND_INPUT)
        assert response.status_code == 200, response.text
        assert queued[-1].report_id == response.json()["data"]["report_id"]
        return queued[-1], headers

    return submit


async def execute(client, report_id, token, body=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return await client.post(
        f"/api/v1/internal/report-jobs/{report_id}/execute",
        headers=headers,
        json=body if body is not None else {"report_id": report_id},
    )


def altered_token(token, **changes):
    claims = jwt.decode(token, options={"verify_signature": False})
    claims.update(changes)
    return jwt.encode(claims, TEST_SECRET, algorithm="HS256")


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_kind", [
    "missing", "demo", "tampered", "audience", "purpose", "issuer", "expired", "missing_exp",
])
async def test_invalid_token_never_calls_pipeline(client, pipeline_calls, invalid_kind):
    token = report_job_token.issue_report_job_token(BRAND_INPUT, "owner-1", "report-1")
    if invalid_kind == "missing":
        token = None
    elif invalid_kind == "demo":
        token = "dev-user-owner-1"
    elif invalid_kind == "tampered":
        parts = token.split(".")
        parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        token = ".".join(parts)
    elif invalid_kind == "missing_exp":
        claims = jwt.decode(token, options={"verify_signature": False})
        claims.pop("exp")
        token = jwt.encode(claims, TEST_SECRET, algorithm="HS256")
    else:
        changes = {
            "audience": {"aud": "some-other-api"},
            "purpose": {"purpose": "some-other-operation"},
            "issuer": {"iss": "some-other-issuer"},
            "expired": {"iat": int(time.time()) - 600, "exp": int(time.time()) - 300},
        }
        token = altered_token(token, **changes[invalid_kind])
    response = await execute(client, "report-1", token)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert pipeline_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("body,path,expected", [
    ({"report_id": "report-2"}, "report-1", 403),
    ({"report_id": "report-2"}, "report-2", 403),
    ({"report_id": "report-1", "user_id": "attacker"}, "report-1", 422),
    ({"report_id": "report-1", "brand_input": BRAND_INPUT}, "report-1", 422),
])
async def test_worker_cannot_swap_report_owner_or_input(client, pipeline_calls, body, path, expected):
    token = report_job_token.issue_report_job_token(BRAND_INPUT, "owner-1", "report-1")
    response = await execute(client, path, token, body)
    assert response.status_code == expected
    assert pipeline_calls == []


@pytest.mark.asyncio
async def test_signed_input_executes_once_and_replay_is_conflict(client, monkeypatch, submit_job):
    job, headers = await submit_job("job-complete")
    calls = []

    def diagnostic(brand_input):
        calls.append(brand_input)
        return {"seo": {"score": 84}, "overall_score": 84, "_costs": []}

    monkeypatch.setattr(report_pipeline, "_run_diagnostic", diagnostic)
    response = await execute(client, job.report_id, job.job_token)
    assert response.status_code == 200
    assert response.json() == {"report_id": job.report_id, "status": "complete"}
    duplicate = await execute(client, job.report_id, job.job_token)
    assert duplicate.status_code == 409
    assert calls == [BRAND_INPUT]
    report = await client.get(f"/api/v1/reports/{job.report_id}", headers=headers)
    assert report.json()["data"]["status"] == "complete"
    assert report.json()["data"]["scores"]["seo"] == 84


@pytest.mark.asyncio
async def test_concurrent_claims_call_provider_once(client, monkeypatch, submit_job):
    job, _ = await submit_job("job-concurrent")
    calls = []

    def diagnostic(brand_input):
        calls.append(brand_input)
        return {"overall_score": 84}

    monkeypatch.setattr(report_pipeline, "_run_diagnostic", diagnostic)
    responses = await asyncio.gather(
        execute(client, job.report_id, job.job_token),
        execute(client, job.report_id, job.job_token),
    )
    assert sorted(response.status_code for response in responses) == [200, 409]
    assert calls == [BRAND_INPUT]


@pytest.mark.asyncio
async def test_signed_wrong_owner_cannot_claim_report(client, monkeypatch, submit_job):
    job, headers = await submit_job("job-owned")
    wrong_owner_token = report_job_token.issue_report_job_token(
        BRAND_INPUT, "another-application-user", job.report_id,
    )
    calls = []

    def diagnostic(brand_input):
        calls.append(brand_input)
        return {}

    monkeypatch.setattr(report_pipeline, "_run_diagnostic", diagnostic)
    response = await execute(client, job.report_id, wrong_owner_token)
    assert response.status_code == 409
    assert calls == []
    report = await client.get(f"/api/v1/reports/{job.report_id}", headers=headers)
    assert report.json()["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_engine_failure_is_sanitized_and_cannot_reexecute(client, monkeypatch, submit_job):
    job, headers = await submit_job("job-failed")
    calls = []

    def diagnostic(brand_input):
        calls.append(brand_input)
        raise RuntimeError("private provider details must never reach report output")

    monkeypatch.setattr(report_pipeline, "_run_diagnostic", diagnostic)
    response = await execute(client, job.report_id, job.job_token)
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    report = await client.get(f"/api/v1/reports/{job.report_id}", headers=headers)
    assert report.json()["data"]["status"] == "failed"
    assert report.json()["data"]["error_message"] == "Analysis failed"
    assert "private provider details" not in report.text
    assert (await execute(client, job.report_id, job.job_token)).status_code == 409
    assert calls == [BRAND_INPUT]


@pytest.mark.asyncio
async def test_completion_persistence_failure_finalizes_safe_status(client, monkeypatch, submit_job):
    job, headers = await submit_job("job-completion-failed")
    monkeypatch.setattr(report_pipeline, "_run_diagnostic", lambda _: {"overall_score": 70})

    async def completion_failure(*args, **kwargs):
        raise RuntimeError("private persistence details")

    monkeypatch.setattr(report_pipeline.report_runs, "complete", completion_failure)
    response = await execute(client, job.report_id, job.job_token)
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    report = await client.get(f"/api/v1/reports/{job.report_id}", headers=headers)
    assert report.json()["data"]["status"] == "failed"
    assert report.json()["data"]["error_message"] == "Analysis failed"
    assert "private persistence details" not in report.text


@pytest.mark.asyncio
async def test_worker_calls_the_internal_http_contract_with_mock_transport():
    from app.jobs import report_worker

    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"report_id": "worker-report", "status": "complete"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as worker_client:
        await report_worker.generate_report(
            {"http_client": worker_client}, "worker-report", "worker-token",
        )

    assert len(requests) == 1
    assert str(requests[0].url) == "http://test/api/v1/internal/report-jobs/worker-report/execute"
    assert requests[0].headers["authorization"] == "Bearer worker-token"
    assert json.loads(requests[0].content) == {"report_id": "worker-report"}


@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [
    ("REPORT_JOB_SECRET", None),
    ("REPORT_JOB_SECRET", "too-short"),
    ("INTERNAL_API_ORIGIN", None),
    ("INTERNAL_API_ORIGIN", "http://user:password@test"),
    ("REPORT_JOB_TOKEN_TTL_SECONDS", 0),
])
async def test_missing_runtime_configuration_does_not_debit(client, monkeypatch, field, value):
    headers = {"Authorization": f"Bearer dev-user-config-{field.lower()}"}
    before = await client.get("/api/v1/credits", headers=headers)
    assert before.status_code == 200
    monkeypatch.setattr(settings, field, value)
    response = await client.post("/api/v1/brands/analyze", headers=headers, json=BRAND_INPUT)
    assert response.status_code == 503
    after = await client.get("/api/v1/credits", headers=headers)
    assert after.json()["data"]["balance"] == before.json()["data"]["balance"]


def test_internal_execution_openapi_has_typed_contract_and_errors():
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/internal/report-jobs/{report_id}/execute"]["post"]
    assert operation["tags"] == ["internal-report-jobs"]
    assert operation["security"] == [{"ReportJobBearer": []}]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ReportJobExecutionRequest"
    )
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ReportJobExecutionResponse"
    )
    assert {"401", "403", "409", "422", "503"} <= operation["responses"].keys()
    assert schema["components"]["schemas"]["ReportJobExecutionRequest"]["additionalProperties"] is False
