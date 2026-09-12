"""Public identity-provider readiness without secret configuration values."""
from typing import Literal
from pydantic import BaseModel


class IdentityHealthData(BaseModel):
    status: Literal["ok", "unconfigured"]
    mode: Literal["demo", "clerk", "unconfigured"]
    auth_provider: str
