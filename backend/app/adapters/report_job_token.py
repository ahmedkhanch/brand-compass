"""Issue and verify narrowly scoped server signatures for report jobs."""

import time
from urllib.parse import urlsplit

import jwt
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import settings
from app.schemas.report_job import ReportJobClaims

JOB_AUDIENCE = "radaros-report-api"
JOB_PURPOSE = "report-execution"
JOB_ISSUER = "radaros-report-submission"


class JobTokenUnavailable(RuntimeError):
    """Server signing configuration cannot safely authorize a job."""


class InvalidJobToken(ValueError):
    """Token does not authorize this exact execution request."""


def _secret() -> str:
    secret = settings.REPORT_JOB_SECRET
    if not secret or len(secret.encode("utf-8")) < 32:
        raise JobTokenUnavailable("Report job signing requires a secret of at least 32 bytes")
    return secret


def require_runtime_configuration() -> None:
    """Reject an unconfigured dispatch boundary before submission takes credit."""
    try:
        _secret()
        origin = urlsplit(settings.INTERNAL_API_ORIGIN or "")
        if (
            origin.scheme not in {"http", "https"}
            or not origin.hostname
            or origin.username is not None
            or origin.password is not None
            or origin.path not in {"", "/"}
            or origin.query
            or origin.fragment
            or not 1 <= settings.REPORT_JOB_TOKEN_TTL_SECONDS <= 3600
        ):
            raise JobTokenUnavailable("Invalid report job runtime configuration")
        # Accessing port also validates malformed/non-numeric port settings.
        origin.port
    except (JobTokenUnavailable, ValueError):
        raise HTTPException(503, "Report job execution is not configured") from None


def issue_report_job_token(brand_input: dict[str, str], user_id: str, report_id: str) -> str:
    """Sign only the owner, report and immutable input approved by submission."""
    secret = _secret()
    ttl = settings.REPORT_JOB_TOKEN_TTL_SECONDS
    if not 1 <= ttl <= 3600:
        raise JobTokenUnavailable("Report job token lifetime must be between 1 and 3600 seconds")
    request = ReportJobClaims(user_id=user_id, report_id=report_id, brand_input=brand_input)
    now = int(time.time())
    return jwt.encode(
        {
            "iss": JOB_ISSUER,
            "aud": JOB_AUDIENCE,
            "purpose": JOB_PURPOSE,
            "sub": user_id,
            "report_id": report_id,
            "brand_input": request.brand_input.model_dump(),
            "iat": now,
            "exp": now + ttl,
        },
        secret,
        algorithm="HS256",
    )


def verify_report_job_token(token: str) -> ReportJobClaims:
    """Reject identity/demo tokens and any alteration of the approved job."""
    secret = _secret()
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=JOB_AUDIENCE,
            issuer=JOB_ISSUER,
            options={
                "require": ["iss", "aud", "purpose", "sub", "report_id", "brand_input", "iat", "exp"],
                "strict_aud": True,
            },
        )
        signed_request = ReportJobClaims(
            user_id=claims["sub"], report_id=claims["report_id"], brand_input=claims["brand_input"],
        )
        if (
            claims["purpose"] != JOB_PURPOSE
            or type(claims["iat"]) is not int
            or type(claims["exp"]) is not int
            or not 0 < claims["exp"] - claims["iat"] <= 3600
        ):
            raise InvalidJobToken("Invalid report job token")
        return signed_request
    except (jwt.PyJWTError, ValidationError, TypeError, KeyError, ValueError):
        raise InvalidJobToken("Invalid report job token") from None
