"""Cryptographic JWT tests: only the public-key fetch is stubbed."""
import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from .conftest import bearer

pytestmark = pytest.mark.asyncio
REAL_KEY_LOOKUP = jwt.PyJWKClient.get_signing_key_from_jwt
ISSUER = "https://identity.example.invalid"


@pytest.fixture
def signed_identity(monkeypatch):
    from app.config import settings
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "ALLOW_DEMO_AUTH", False)
    monkeypatch.setattr(settings, "CLERK_JWT_ISSUER", ISSUER)
    monkeypatch.setattr(settings, "CLERK_JWT_AUDIENCE", "radaros")
    monkeypatch.setattr(settings, "CLERK_AUTHORIZED_PARTIES", "https://app.example.invalid")
    monkeypatch.setattr(jwt.PyJWKClient, "get_signing_key_from_jwt",
                        lambda self, token: SimpleNamespace(key=private_key.public_key()))
    claims = {"sub": "user_clerk_verified", "iss": ISSUER, "iat": int(time.time())-5,
              "exp": int(time.time())+300, "aud": "radaros", "azp": "https://app.example.invalid"}
    return private_key, claims


async def test_verified_clerk_jwt_can_read_own_history(client, signed_identity):
    key, claims = signed_identity
    token = jwt.encode(claims, key, algorithm="RS256")
    assert (await client.get("/api/v1/reports", headers=bearer(token))).status_code == 200


@pytest.mark.parametrize("field,value", [
    ("iss", "https://wrong.example.invalid"), ("exp", 1), ("iat", 9999999999),
    ("aud", "other-app"), ("azp", "https://other.example.invalid"), ("sub", ""), ("sub", 42),
])
async def test_invalid_claims_are_rejected(client, signed_identity, field, value):
    key, claims = signed_identity
    claims[field] = value
    token = jwt.encode(claims, key, algorithm="RS256")
    response = await client.get("/api/v1/reports", headers=bearer(token))
    assert response.status_code == 401
    assert token not in response.text


@pytest.mark.parametrize("missing", ["sub", "exp", "iss", "iat", "azp"])
async def test_required_claims_cannot_be_omitted(client, signed_identity, missing):
    key, claims = signed_identity
    del claims[missing]
    response = await client.get("/api/v1/reports", headers=bearer(jwt.encode(claims, key, algorithm="RS256")))
    assert response.status_code == 401


async def test_wrong_signature_is_rejected(client, signed_identity):
    _, claims = signed_identity
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(claims, other_key, algorithm="RS256")
    assert (await client.get("/api/v1/reports", headers=bearer(token))).status_code == 401


async def test_wrong_algorithm_is_rejected(client, signed_identity):
    _, claims = signed_identity
    token = jwt.encode(claims, "fixture-secret-at-least-32-bytes-long", algorithm="HS256")
    assert (await client.get("/api/v1/reports", headers=bearer(token))).status_code == 401


async def test_missing_identity_config_fails_closed(client, signed_identity, monkeypatch):
    from app.config import settings
    key, claims = signed_identity
    monkeypatch.setattr(settings, "CLERK_JWT_ISSUER", None)
    response = await client.get("/api/v1/reports", headers=bearer(jwt.encode(claims, key, algorithm="RS256")))
    assert response.status_code == 503


async def test_identity_provider_outage_is_not_anonymous_fallback(client, signed_identity, monkeypatch):
    key, claims = signed_identity
    def unavailable(self, token):
        raise jwt.PyJWKClientConnectionError("PRIVATE_ERROR")
    monkeypatch.setattr(jwt.PyJWKClient, "get_signing_key_from_jwt", unavailable)
    response = await client.get("/api/v1/reports", headers=bearer(jwt.encode(claims, key, algorithm="RS256")))
    assert response.status_code == 503
    assert "PRIVATE_ERROR" not in response.text


async def test_missing_authorized_parties_fails_closed(client, signed_identity, monkeypatch):
    from app.config import settings
    key, claims = signed_identity
    monkeypatch.setattr(settings, "CLERK_AUTHORIZED_PARTIES", "")
    response = await client.get("/api/v1/reports", headers=bearer(jwt.encode(claims, key, algorithm="RS256")))
    assert response.status_code == 503
    assert (await client.get("/api/v1/health")).json()["data"]["mode"] == "unconfigured"


@pytest.mark.parametrize("kid,expected", [("known-key", 200), ("unknown-key", 401)])
async def test_jwks_selects_only_matching_public_key(client, signed_identity, monkeypatch, kid, expected):
    from app.core.identity import jwks_client
    key, claims = signed_identity
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    jwk.update(kid="known-key", use="sig", alg="RS256")
    jwks_client.cache_clear()
    monkeypatch.setattr(jwt.PyJWKClient, "get_signing_key_from_jwt", REAL_KEY_LOOKUP)
    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", lambda self: {"keys": [jwk]})
    token = jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})
    assert (await client.get("/api/v1/reports", headers=bearer(token))).status_code == expected
    jwks_client.cache_clear()
