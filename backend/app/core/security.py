"""Security scheme for Swagger UI — shows the Authorize button."""

from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Enter 'dev-user-anything' for local dev, or a real Clerk JWT in production.",
    auto_error=False,
)
