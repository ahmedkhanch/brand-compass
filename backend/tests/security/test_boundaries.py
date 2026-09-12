"""Regression tests exercise identity, ownership and entitlement at the HTTP boundary."""
import uuid

import pytest
from .conftest import bearer

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer garbage"}, {"Authorization": "Basic Zm9vOmJhcg=="}])
async def test_missing_or_invalid_identity_is_rejected(client, headers):
    response = await client.get("/api/v1/reports", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_demo_identity_requires_both_explicit_switches(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert (await client.get("/api/v1/reports", headers=bearer("dev-user-unsafe"))).status_code == 401
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "ALLOW_DEMO_AUTH", False)
    assert (await client.get("/api/v1/reports", headers=bearer("dev-user-unsafe"))).status_code == 401


async def test_demo_identity_works_only_in_isolated_demo(client):
    response = await client.get("/api/v1/reports", headers=bearer("dev-user-allowed"))
    assert response.status_code == 200


async def test_foreign_report_is_hidden_from_every_read_path(client, report):
    intruder = bearer("dev-user-" + uuid.uuid4().hex)
    for suffix in [f"/api/v1/reports/{report.report_id}", f"/api/v1/reports/{report.report_id}/meta-ads", f"/sse/reports/{report.report_id}"]:
        response = await client.get(suffix, headers=intruder)
        assert response.status_code == 404, (suffix, response.text)
        assert report.report_id not in response.text
        assert "PRIVATE_AD" not in response.text
    listing = await client.get("/api/v1/reports", headers=intruder)
    assert report.report_id not in listing.text
    assert (await client.delete(f"/api/v1/reports/{report.report_id}", headers=intruder)).status_code == 404
    assert (await client.get(f"/api/v1/reports/{report.report_id}", headers=bearer(report.owner))).status_code == 200


async def test_owner_can_stream_and_delete_own_report(client, report):
    headers = bearer(report.owner)
    stream = await client.get(f"/sse/reports/{report.report_id}", headers=headers)
    assert stream.status_code == 200
    assert "text/event-stream" in stream.headers["content-type"]
    assert '"status": "complete"' in stream.text
    assert "PRIVATE_AD" not in stream.text
    assert (await client.delete(f"/api/v1/reports/{report.report_id}", headers=headers)).status_code == 200
    assert (await client.get(f"/sse/reports/{report.report_id}", headers=headers)).status_code == 404


async def test_base_tier_never_receives_paid_data_or_internal_costs(client, report):
    headers = bearer(report.owner)
    response = await client.get(f"/api/v1/reports/{report.report_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["payload"]["seo"]["score"] == 65
    assert "PRIVATE_AD" not in response.text
    assert "INTERNAL_COST" not in response.text
    assert (await client.get(f"/api/v1/reports/{report.report_id}/meta-ads", headers=headers)).status_code == 402


async def test_entitled_owner_receives_ads_and_downgrade_takes_effect(client, report):
    headers = bearer(report.owner)
    await client.post("/__fixture/report", json={"owner": report.owner, "tier": "radar"})
    assert "PRIVATE_AD" in (await client.get(f"/api/v1/reports/{report.report_id}", headers=headers)).text
    assert "PRIVATE_AD" in (await client.get(f"/api/v1/reports/{report.report_id}/meta-ads", headers=headers)).text
    await client.post("/__fixture/report", json={"owner": report.owner, "tier": "boussole"})
    assert "PRIVATE_AD" not in (await client.get(f"/api/v1/reports/{report.report_id}", headers=headers)).text


async def test_direct_upgrade_cannot_change_subscription_or_credits(client, report):
    headers = bearer(report.owner)
    before = (await client.get("/api/v1/credits", headers=headers)).json()["data"]["balance"]
    for tier in ["radar", "stratege"]:
        response = await client.post("/api/v1/subscription/upgrade", params={"tier": tier}, headers=headers)
        assert response.status_code == 403
    after = (await client.get("/api/v1/credits", headers=headers)).json()["data"]["balance"]
    assert after == before
    assert (await client.get("/api/v1/subscription", headers=headers)).json()["data"]["tier"] == "boussole"


async def test_new_user_has_no_paid_subscription(client):
    response = await client.get("/api/v1/subscription", headers=bearer("dev-user-"+uuid.uuid4().hex))
    assert response.status_code == 200
    assert response.json()["data"]["tier"] == "boussole"


async def test_touched_api_contracts_are_documented_and_typed(client):
    schema = (await client.get("/openapi.json")).json()
    for route, method in [("/api/v1/reports", "get"), ("/api/v1/reports/{report_id}", "get"),
                          ("/api/v1/reports/{report_id}", "delete"), ("/api/v1/reports/{report_id}/meta-ads", "get"),
                          ("/api/v1/subscription", "get"), ("/api/v1/subscription/upgrade", "post"),
                          ("/sse/reports/{report_id}", "get")]:
        operation = schema["paths"][route][method]
        assert operation["tags"] and operation["summary"] and operation["description"]
        assert "401" in operation["responses"]
    assert "402" in schema["paths"]["/api/v1/reports/{report_id}/meta-ads"]["get"]["responses"]
    assert (await client.get("/docs")).status_code == 200
    assert (await client.get("/redoc")).status_code == 404


async def test_reading_reports_does_not_consume_credit(client, report):
    headers = bearer(report.owner)
    before = (await client.get("/api/v1/credits", headers=headers)).json()["data"]["balance"]
    for _ in range(3):
        assert (await client.get(f"/api/v1/reports/{report.report_id}", headers=headers)).status_code == 200
    assert (await client.get("/api/v1/credits", headers=headers)).json()["data"]["balance"] == before


async def test_deleting_report_during_stream_stops_without_leaking(client, monkeypatch):
    import asyncio
    from app.services import report_progress
    owner = "dev-user-" + uuid.uuid4().hex
    report = (await client.post("/__fixture/report", json={"owner": owner, "status": "running"})).json()
    headers = bearer(owner)
    monkeypatch.setattr(report_progress, "POLL_SECONDS", 0.01)
    stream = asyncio.create_task(client.get(f'/sse/reports/{report["report_id"]}', headers=headers))
    await asyncio.sleep(0.08)
    assert (await client.delete(f'/api/v1/reports/{report["report_id"]}', headers=headers)).status_code == 200
    response = await asyncio.wait_for(stream, timeout=2)
    assert response.status_code == 200
    assert "Report not found" in response.text
    assert "PRIVATE_AD" not in response.text


@pytest.mark.parametrize("query", ["page=0", "page_size=0", "page_size=101"])
async def test_history_pagination_is_bounded(client, query):
    assert (await client.get("/api/v1/reports?"+query, headers=bearer("dev-user-paging"))).status_code == 422


async def test_unconfigured_legacy_webhook_stub_does_not_mutate_rights(client, report):
    payload = {"type": "checkout.session.completed", "data": {"object": {
        "customer_email": "fixture@example.invalid", "metadata": {"user_id": report.user_id, "tier": "stratege"}
    }}}
    # This explicitly exercises the historical stub, not signature verification.
    receipt = await client.post("/api/v1/webhooks/stripe", json=payload, headers={"stripe-signature": "forged"})
    assert receipt.status_code == 200
    assert receipt.json()["meta"]["mode"] == "stub"
    response = await client.get("/api/v1/subscription", headers=bearer(report.owner))
    assert response.json()["data"]["tier"] == "boussole"


async def test_account_responses_are_not_cacheable(client, report):
    for headers in [bearer(report.owner), {}, bearer("dev-user-other-cache")]:
        response = await client.get(f"/api/v1/reports/{report.report_id}", headers=headers)
        assert response.headers["cache-control"] == "private, no-store"
        assert "authorization" in response.headers["vary"].lower()


async def test_provider_failure_is_unavailable_without_internal_error(client, monkeypatch):
    from engine.providers import mock, apify
    owner = "dev-user-" + uuid.uuid4().hex
    fixture = (await client.post("/__fixture/report", json={"owner": owner, "tier": "radar", "has_ads": False})).json()
    monkeypatch.setattr(mock, "provider_ready", lambda name: True)
    monkeypatch.setattr(apify.ApifyProvider, "__init__", lambda self: None)
    def failed(self, *args, **kwargs):
        raise TimeoutError("PRIVATE_PROVIDER_ERROR")
    monkeypatch.setattr(apify.ApifyProvider, "search_meta_ads", failed)
    response = await client.get(f'/api/v1/reports/{fixture["report_id"]}/meta-ads', headers=bearer(owner))
    assert response.status_code == 200
    assert response.json()["data"]["availability"] == "unavailable"
    assert response.json()["data"]["meta_ads"] is None
    assert "PRIVATE_PROVIDER_ERROR" not in response.text


async def test_concurrent_identity_resolution_uses_one_account(client):
    import asyncio
    owner = "dev-user-" + uuid.uuid4().hex
    responses = await asyncio.gather(*(client.get("/api/v1/auth/me", headers=bearer(owner)) for _ in range(4)))
    assert all(r.status_code == 200 for r in responses)
    assert len({r.json()["data"]["user_id"] for r in responses}) == 1
