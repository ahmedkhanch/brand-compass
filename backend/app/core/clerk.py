"""Compatibility adapter sharing the canonical identity verifier."""
from fastapi import Request
from app.core.identity import authenticate


async def verify_clerk_token(request: Request) -> str:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    return await authenticate(token.strip() if scheme.lower() == "bearer" else "")
