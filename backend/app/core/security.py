"""Security scheme for Swagger UI — shows the Authorize button."""

from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Clerk JWT required. Local dev-user-* tokens require both DEMO_MODE and ALLOW_DEMO_AUTH; never accepted otherwise.",
    auto_error=False,
)
