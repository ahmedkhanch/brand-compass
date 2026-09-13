"""Aggregates all v1 API routes."""

from fastapi import APIRouter
from app.api.v1 import auth, brands, reports, credits, subscriptions, webhooks, report_jobs

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, tags=["auth"])
router.include_router(brands.router, tags=["brands"])
router.include_router(reports.router, tags=["reports"])
router.include_router(credits.router, tags=["credits"])
router.include_router(subscriptions.router, tags=["subscriptions"])
router.include_router(webhooks.router, tags=["webhooks"])
router.include_router(report_jobs.router, tags=["internal-report-jobs"])
