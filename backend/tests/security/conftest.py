"""HTTP-only integration fixtures backed by an Alembic-created temporary database."""
import os
import subprocess
import uuid
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select


class FixtureInput(BaseModel):
    owner: str
    tier: str = "boussole"
    status: str = "complete"
    has_ads: bool = True


async def seed_fixture_service(db, data):
    # Test-only service, reached through the fixture API registered below.
    from app.models import User, Brand, Report, ReportStatus, Subscription, TierEnum, Credit
    user = (await db.execute(select(User).where(User.clerk_user_id == data.owner))).scalar_one_or_none()
    if user is None:
        user = User(id=str(uuid.uuid4()), clerk_user_id=data.owner, email=f"{data.owner}@fixture.invalid")
        db.add(user)
        await db.flush()
    sub = (await db.execute(select(Subscription).where(Subscription.user_id == user.id))).scalar_one_or_none()
    if sub:
        sub.tier = TierEnum(data.tier)
    else:
        db.add(Subscription(user_id=user.id, tier=TierEnum(data.tier), status="active"))
    credit = (await db.execute(select(Credit).where(Credit.user_id == user.id))).scalar_one_or_none()
    if credit is None:
        db.add(Credit(user_id=user.id, balance=7))
    brand = Brand(id=str(uuid.uuid4()), user_id=user.id, name="Fixture brand")
    db.add(brand)
    await db.flush()
    report = Report(id=str(uuid.uuid4()), user_id=user.id, brand_id=brand.id, status=ReportStatus(data.status),
                    payload={"brand": "Fixture brand", "seo": {"score": 65},
                             "meta_ads": {"ads": [{"ad_text": "PRIVATE_AD"}], "total_ads_found": 1},
                             "_costs": [{"provider": "INTERNAL_COST"}]}, scores={"seo": 65})
    if not data.has_ads:
        report.payload = {k: v for k, v in report.payload.items() if k != "meta_ads"}
    db.add(report)
    await db.flush()
    return {"report_id": report.id, "user_id": user.id}


@pytest.fixture(scope="session")
def security_app(tmp_path_factory):
    from app.config import settings
    database = tmp_path_factory.mktemp("security") / "security.db"
    url = f"sqlite+aiosqlite:///{database}"
    settings.DATABASE_URL = url
    settings.DEBUG = False
    settings.DEMO_MODE = True
    settings.ALLOW_DEMO_AUTH = True
    subprocess.run(["python", "-m", "alembic", "upgrade", "head"], check=True,
                   env={**os.environ, "DATABASE_URL": url}, capture_output=True)
    from app.main import app
    from app.database import get_db

    @app.post("/__fixture/report", include_in_schema=False)
    async def fixture_report(data: FixtureInput, db=Depends(get_db)):
        return await seed_fixture_service(db, data)

    return app


@pytest_asyncio.fixture
async def client(security_app, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "ALLOW_DEMO_AUTH", True)
    monkeypatch.setattr(settings, "CLERK_JWT_ISSUER", None)
    monkeypatch.setattr(settings, "CLERK_SECRET_KEY", None)
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", None)
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=security_app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def report(client):
    owner = "dev-user-" + uuid.uuid4().hex
    response = await client.post("/__fixture/report", json={"owner": owner})
    assert response.status_code == 200
    return SimpleNamespace(owner=owner, **response.json())


def bearer(subject):
    return {"Authorization": f"Bearer {subject}"}
