"""
Manual report repair tool.
Runs the diagnostic pipeline for a stuck report and saves results.
Useful when a background task silently fails.

Usage:
  cd backend
  python repair_report.py <report_id>
  python repair_report.py d804177c-b12e-4246-9fcc-92e8811264c5
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend/ is on path and .env is loaded
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from sqlalchemy import select
from app.models import Report, ReportStatus, Brand
from app.database import async_session_factory
from engine.orchestrator import run_full_diagnostic


async def repair(report_id: str):
    print(f"[INFO] Looking for report {report_id}...")

    async with async_session_factory() as db:
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            print(f"[FAIL] Report {report_id} not found")
            return

        # Get brand info
        brand_result = await db.execute(
            select(Brand).where(Brand.id == report.brand_id)
        )
        brand = brand_result.scalar_one_or_none()
        if not brand:
            print("[FAIL] Brand not found")
            return

        print(f"[INFO] Brand: {brand.name}")
        print(f"[INFO] Website: {brand.website_url}")
        print(f"[INFO] Current status: {report.status.value}")

        try:
            # Mark as running
            report.status = ReportStatus.RUNNING
            await db.commit()
            print("[INFO] Status set to RUNNING")

            # Run pipeline (sync, blocks but this is a script, not a server)
            print("[INFO] Running full diagnostic pipeline...")
            print("[INFO] This takes 40-90 seconds...")
            sys.stdout.flush()

            diagnostic = run_full_diagnostic(
                brand_name=brand.name,
                website_url=brand.website_url or "",
                industry="",
                competitor="",
            )

            # Save results
            report.status = ReportStatus.COMPLETE
            report.payload = diagnostic
            report.scores = {
                "seo": diagnostic.get("seo", {}).get("score") if diagnostic.get("seo") else None,
                "geo": diagnostic.get("geo", {}).get("score") if diagnostic.get("geo") else None,
                "overall": diagnostic.get("overall_score"),
            }
            report.generated_at = datetime.now(timezone.utc)
            await db.commit()

            print(f"[OK] Report COMPLETE!")
            print(f"     Overall score: {diagnostic.get('overall_score')}")
            print(f"     SEO: {diagnostic.get('seo', {}).get('score')}")
            print(f"     GEO: {diagnostic.get('geo', {}).get('score')}")
            se = diagnostic.get("website_content", {}).get("error")
            pe = diagnostic.get("positioning", {}).get("error") if isinstance(diagnostic.get("positioning"), dict) else None
            if se:
                print(f"     Warnings: website_content={se}")
            if pe:
                print(f"               positioning={pe}")

        except Exception as e:
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            await db.commit()
            print(f"[FAIL] Pipeline failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python repair_report.py <report_id>")
        print("Example: python repair_report.py d804177c-b12e-4246-9fcc-92e8811264c5")
        sys.exit(1)

    asyncio.run(repair(sys.argv[1]))
