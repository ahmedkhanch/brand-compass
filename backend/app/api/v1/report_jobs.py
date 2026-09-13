"""Internal HTTP boundary for server-authorized report execution."""

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.adapters.report_job_token import (
    InvalidJobToken,
    JobTokenUnavailable,
    verify_report_job_token,
)
from app.schemas.report_job import (
    ReportJobError,
    ReportJobExecutionRequest,
    ReportJobExecutionResponse,
)
from app.services import report_pipeline

router = APIRouter()
job_bearer = HTTPBearer(
    scheme_name="ReportJobBearer",
    description="Short-lived server-signed token scoped to one report, owner, and brand input.",
    auto_error=False,
)


@router.post(
    "/internal/report-jobs/{report_id}/execute",
    response_model=ReportJobExecutionResponse,
    summary="Execute a server-authorized report job",
    description=(
        "Verifies the job token's signature, expiry, audience, purpose, report ID, owner, "
        "and signed brand input before calling the pipeline service. Owner and executable "
        "input come exclusively from verified claims. The service atomically claims an "
        "owned queued report; duplicate requests return 409 without repeating execution. "
        "A 200 response reports complete or failed execution. Clerk and demo "
        "identity tokens cannot authorize this operation."
    ),
    responses={
        401: {"model": ReportJobError, "description": "Missing, expired, invalid or incorrectly scoped job token"},
        403: {"model": ReportJobError, "description": "Requested report does not match the signed report"},
        409: {"model": ReportJobError, "description": "Owned queued report could not be claimed"},
        503: {"model": ReportJobError, "description": "Job signing or terminal report persistence is unavailable"},
    },
)
async def execute_report_job(
    report_id: str,
    request: ReportJobExecutionRequest,
    credentials: HTTPAuthorizationCredentials | None = Security(job_bearer),
) -> ReportJobExecutionResponse:
    try:
        if credentials is None:
            raise InvalidJobToken("Missing report job token")
        claims = verify_report_job_token(credentials.credentials)
    except JobTokenUnavailable:
        raise HTTPException(503, "Report job authentication is not configured") from None
    except InvalidJobToken:
        raise HTTPException(
            401, "Missing or invalid report job token", headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if request.report_id != report_id or claims.report_id != report_id:
        raise HTTPException(403, "Report does not match job authorization")

    try:
        status = await report_pipeline.execute(claims.brand_input.model_dump(), claims.user_id, report_id)
    except report_pipeline.ReportPersistenceUnavailable:
        raise HTTPException(503, "Report execution state could not be finalized") from None
    if status == "not_claimed":
        raise HTTPException(409, "Owned queued report could not be claimed")
    return ReportJobExecutionResponse(report_id=report_id, status=status)
