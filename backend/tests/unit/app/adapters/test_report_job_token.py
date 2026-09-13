"""Signing rejects unsafe settings and verifies strict claim types."""

import time

import jwt
import pytest
from fastapi import HTTPException

from app.adapters import report_job_token as tokens
from app.config import settings

SECRET = "synthetic-unit-test-signing-secret-with-32-bytes"
BRAND = {"name": "Unit brand", "website_url": "", "industry": "", "competitor": ""}


@pytest.fixture(autouse=True)
def configure(monkeypatch):
    monkeypatch.setattr(settings, "REPORT_JOB_SECRET", SECRET)
    monkeypatch.setattr(settings, "REPORT_JOB_TOKEN_TTL_SECONDS", 300)
    monkeypatch.setattr(settings, "INTERNAL_API_ORIGIN", "http://test")


@pytest.mark.parametrize("ttl", [0, 1, 29, 3601])
def test_signer_rejects_unsupported_lifetime(monkeypatch, ttl):
    monkeypatch.setattr(settings, "REPORT_JOB_TOKEN_TTL_SECONDS", ttl)
    with pytest.raises(tokens.JobTokenUnavailable):
        tokens.issue_report_job_token(BRAND, "owner", "report")


@pytest.mark.parametrize("origin", ["file:///tmp/api", "http://test:bad", "http://test/path", "http://test?q=1", "http://test#x"])
def test_configuration_rejects_non_origin_urls(monkeypatch, origin):
    monkeypatch.setattr(settings, "INTERNAL_API_ORIGIN", origin)
    with pytest.raises(HTTPException) as error:
        tokens.require_runtime_configuration()
    assert error.value.status_code == 503


@pytest.mark.parametrize("change", [
    {"exp": str(int(time.time()) + 300)},
    {"iat": str(int(time.time()))},
    {"exp": int(time.time()) + 4000},
    {"brand_input": {"name": "broken"}},
    {"sub": ""},
])
def test_verifier_rejects_signed_malformed_claims(change):
    token = tokens.issue_report_job_token(BRAND, "owner", "report")
    claims = jwt.decode(token, options={"verify_signature": False})
    claims.update(change)
    with pytest.raises(tokens.InvalidJobToken):
        tokens.verify_report_job_token(jwt.encode(claims, SECRET, algorithm="HS256"))
